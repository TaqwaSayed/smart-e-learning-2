from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name = models.CharField(max_length=150, verbose_name=_('Name'))
    description = models.TextField(blank=True, verbose_name=_('Description'))

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def __str__(self):
        return self.name


class Course(models.Model):
    title = models.CharField(max_length=200, verbose_name=_('Title'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses', verbose_name=_('Category')
    )
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses_taught', verbose_name=_('Instructor')
    )
    total_lessons = models.PositiveIntegerField(default=0, verbose_name=_('Total Lessons'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    class Meta:
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')

    def __str__(self):
        return self.title


class LiveLecture(models.Model):
    title = models.CharField(max_length=200, verbose_name=_('Title'))
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='live_lectures', verbose_name=_('Course'))
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='live_lectures', verbose_name=_('Instructor'))
    scheduled_at = models.DateTimeField(verbose_name=_('Scheduled At'))
    zoom_url = models.URLField(blank=True, default="https://zoom.us/j/smart-elearning", verbose_name=_('Zoom URL'))

    class Meta:
        verbose_name = _('Live Lecture')
        verbose_name_plural = _('Live Lectures')

    def time_remaining(self):
        now = timezone.now()
        if self.scheduled_at > now:
            diff = self.scheduled_at - now
            days = diff.days
            hours = diff.seconds // 3600
            if days > 0:
                return f"{days} d, {hours} h"
            return f"{hours} h"
        return _("Started")

    def __str__(self):
        return f"{self.title} - {self.course.title}"


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons', verbose_name=_('Course'))
    title = models.CharField(max_length=200, verbose_name=_('Title'))
    content = models.TextField(blank=True, verbose_name=_('Content'))
    video_url = models.URLField(blank=True, null=True, verbose_name=_('Video URL'))
    order_number = models.PositiveIntegerField(default=1, verbose_name=_('Order Number'))

    class Meta:
        ordering = ['order_number']
        verbose_name = _('Lesson')
        verbose_name_plural = _('Lessons')

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        COMPLETED = 'COMPLETED', _('Completed')
        PAUSED = 'PAUSED', _('Paused')

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments', verbose_name=_('Student'))
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments', verbose_name=_('Course'))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, verbose_name=_('Status'))
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Enrolled At'))

    class Meta:
        unique_together = ('student', 'course')
        verbose_name = _('Enrollment')
        verbose_name_plural = _('Enrollments')

    def __str__(self):
        return f"{self.student} -> {self.course}"


class CourseProgress(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='course_progress', verbose_name=_('Student'))
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='progress_records', verbose_name=_('Course'))
    last_accessed = models.DateTimeField(auto_now=True, verbose_name=_('Last Accessed'))
    completion_percentage = models.PositiveSmallIntegerField(default=0, verbose_name=_('Completion Percentage'))

    class Meta:
        unique_together = ('student', 'course')
        verbose_name = _('Course Progress')
        verbose_name_plural = _('Course Progresses')


class Quiz(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='quizzes', verbose_name=_('Lesson'))
    title = models.CharField(max_length=200, blank=True, verbose_name=_('Title'))
    passing_score = models.PositiveSmallIntegerField(default=50, verbose_name=_('Passing Score'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    class Meta:
        verbose_name = _('Quiz')
        verbose_name_plural = _('Quizzes')

    def __str__(self):
        return self.title or f"Quiz #{self.pk}"


class Question(models.Model):
    class Difficulty(models.TextChoices):
        EASY = 'EASY', _('Easy')
        MEDIUM = 'MEDIUM', _('Medium')
        HARD = 'HARD', _('Hard')

    topic = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='questions', verbose_name=_('Topic')
    )
    question_text = models.TextField(verbose_name=_('Question Text'))
    correct_answer = models.CharField(max_length=255, blank=True, verbose_name=_('Correct Answer'))
    difficulty_level = models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM, verbose_name=_('Difficulty Level'))
    is_ai_generated = models.BooleanField(default=False, verbose_name=_('Is AI Generated'))

    class Meta:
        verbose_name = _('Question')
        verbose_name_plural = _('Questions')

    def __str__(self):
        return self.question_text[:50]


class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='quiz_questions', verbose_name=_('Quiz'))
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='quiz_links', verbose_name=_('Question'))
    order_number = models.PositiveIntegerField(default=1, verbose_name=_('Order Number'))

    class Meta:
        unique_together = ('quiz', 'question')
        verbose_name = _('Quiz Question')
        verbose_name_plural = _('Quiz Questions')


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices', verbose_name=_('Question'))
    choice_text = models.CharField(max_length=255, verbose_name=_('Choice Text'))
    is_correct = models.BooleanField(default=False, verbose_name=_('Is Correct'))

    class Meta:
        verbose_name = _('Choice')
        verbose_name_plural = _('Choices')

    def __str__(self):
        return self.choice_text


class QuizAttempt(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts', verbose_name=_('Student'))
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts', verbose_name=_('Quiz'))
    score = models.FloatField(null=True, blank=True, verbose_name=_('Score'))
    started_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Started At'))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Completed At'))

    class Meta:
        verbose_name = _('Quiz Attempt')
        verbose_name_plural = _('Quiz Attempts')

    def __str__(self):
        return f"{self.student} - {self.quiz} - {self.score}"


class UserAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers', verbose_name=_('Attempt'))
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='user_answers', verbose_name=_('Question'))
    selected_choice = models.ForeignKey(Choice, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Selected Choice'))
    answer_text = models.CharField(max_length=255, blank=True, verbose_name=_('Answer Text'))
    is_correct = models.BooleanField(default=False, verbose_name=_('Is Correct'))
    answered_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Answered At'))

    class Meta:
        verbose_name = _('User Answer')
        verbose_name_plural = _('User Answers')


class StudentPerformance(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='topic_performances', verbose_name=_('Student'))
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='topic_performances', verbose_name=_('Course'))
    topic = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='performance_records', verbose_name=_('Topic'))
    correct_answers = models.PositiveIntegerField(default=0, verbose_name=_('Correct Answers'))
    wrong_answers = models.PositiveIntegerField(default=0, verbose_name=_('Wrong Answers'))

    class Meta:
        unique_together = ('student', 'course', 'topic')
        verbose_name = _('Student Performance')
        verbose_name_plural = _('Student Performances')

    @property
    def weakness_score(self) -> float:
        total = self.correct_answers + self.wrong_answers
        if total == 0:
            return 0.0
        return self.wrong_answers / total


class StudySession(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='study_sessions', verbose_name=_('Student'))
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='study_sessions', verbose_name=_('Course'))
    start_time = models.DateTimeField(auto_now_add=True, verbose_name=_('Start Time'))
    end_time = models.DateTimeField(null=True, blank=True, verbose_name=_('End Time'))
    duration_minutes = models.PositiveIntegerField(default=0, verbose_name=_('Duration (Minutes)'))

    class Meta:
        verbose_name = _('Study Session')
        verbose_name_plural = _('Study Sessions')


class StudyPlan(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='study_plans', verbose_name=_('Student'))
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='study_plans', verbose_name=_('Course'))
    topic = models.CharField(max_length=200, verbose_name=_('Topic'))
    action_items = models.TextField(verbose_name=_('Action Items'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    class Meta:
        verbose_name = _('Study Plan')
        verbose_name_plural = _('Study Plans')

    def __str__(self):
        return f"{self.student} - {self.topic}"