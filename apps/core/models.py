from django.conf import settings
from django.db import models


class MindfulnessContent(models.Model):
    """Reminders / verses / hadiths shown before, during, or after a study session."""
    class Phase(models.TextChoices):
        BEFORE_STUDY = 'BEFORE', 'Before study'
        DURING_BREAK = 'BREAK', 'During break (every 25 min)'
        AFTER_STUDY = 'AFTER', 'After study'

    text = models.TextField(blank=True, help_text='Optional if an image already contains the text')
    image = models.ImageField(upload_to='mindfulness/', blank=True, null=True)
    source = models.CharField(max_length=150, blank=True)
    phase = models.CharField(max_length=20, choices=Phase.choices, default=Phase.DURING_BREAK)

    def __str__(self):
        return self.text[:40] if self.text else (self.image.name if self.image else f'Item #{self.pk}')


class Badge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    requirement = models.CharField(max_length=255, blank=True)
    icon_emoji = models.CharField(max_length=10, default='🏅')

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='user_badges')
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'badge')


class Goal(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        DONE = 'DONE', 'Done'

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goals')
    goal_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    target_minutes = models.PositiveIntegerField(default=0)
    completed_minutes = models.PositiveIntegerField(default=0)


class DhikrContent(models.Model):
    text = models.TextField()

    def __str__(self):
        return self.text[:40]


class DhikrCompletion(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dhikr_completions')
    dhikr = models.ForeignKey(DhikrContent, on_delete=models.CASCADE, related_name='completions')
    completed_date = models.DateField(auto_now_add=True)
    completed_count = models.PositiveIntegerField(default=0)


class Points(models.Model):
    """Log of every point-earning event for a student (not just a running total)."""
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='points_log')
    points = models.IntegerField()
    reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Points entry'
        verbose_name_plural = 'Points log'


class Level(models.Model):
    name = models.CharField(max_length=100)
    min_points = models.PositiveIntegerField(default=0)
    order_number = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order_number']

    def __str__(self):
        return self.name


class StudentTask(models.Model):
    """
    A task the student typed in themselves (like a personal notepad
    checklist), not tied to any specific course. Checking it off awards
    points.
    """
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks')
    text = models.CharField(max_length=300)
    is_done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['is_done', '-created_at']

    def __str__(self):
        return self.text[:50]


class AIChatSession(models.Model):
    """A conversation thread between a student and the AI tutor."""
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_chat_sessions')
    course = models.ForeignKey('learning.Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_chats')
    created_at = models.DateTimeField(auto_now_add=True)


class AIMessage(models.Model):
    """A single message inside an AIChatSession, from either the student or the AI."""
    class Sender(models.TextChoices):
        USER = 'USER', 'User'
        AI = 'AI', 'AI'

    session = models.ForeignKey(AIChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=Sender.choices)
    message_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
