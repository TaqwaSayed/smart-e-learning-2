from django.contrib import admin
from .models import (
    Category, Course, Lesson, Enrollment, CourseProgress, Quiz, Question,
    QuizQuestion, Choice, QuizAttempt, UserAnswer, StudentPerformance,
    StudySession, StudyPlan,
)

admin.site.register(Category)
admin.site.register(Course)
admin.site.register(Lesson)
admin.site.register(Enrollment)
admin.site.register(CourseProgress)
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(QuizQuestion)
admin.site.register(Choice)
admin.site.register(QuizAttempt)
admin.site.register(UserAnswer)
admin.site.register(StudentPerformance)
admin.site.register(StudySession)
admin.site.register(StudyPlan)
