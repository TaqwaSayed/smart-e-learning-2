from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        INSTRUCTOR = 'INSTRUCTOR', 'Instructor'
        STUDENT = 'STUDENT', 'Student'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    points = models.PositiveIntegerField(default=0)
    study_streak = models.PositiveIntegerField(default=0)
    preferred_language = models.CharField(max_length=5, default='ar')
    # Relationship 20 from the ERD: Level 1:N User
    level = models.ForeignKey(
        'core.Level', on_delete=models.SET_NULL, null=True, blank=True, related_name='users'
    )

    def is_student(self):
        return self.role == self.Role.STUDENT

    def is_instructor(self):
        return self.role == self.Role.INSTRUCTOR

    def add_points(self, amount: int, reason: str = ""):
        """Adds points to the user, logs the event in Points, and updates their Level if needed."""
        from apps.core.models import Points, Level

        Points.objects.create(student=self, points=amount, reason=reason)
        self.points = models.F('points') + amount
        self.save(update_fields=['points'])
        self.refresh_from_db(fields=['points'])

        next_level = (
            Level.objects.filter(min_points__lte=self.points).order_by('-min_points').first()
        )
        if next_level and next_level != self.level:
            self.level = next_level
            self.save(update_fields=['level'])
