from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses_taught'
    )
    total_lessons = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    video_url = models.URLField(blank=True, null=True)
    order_number = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order_number']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        COMPLETED = 'COMPLETED', 'Completed'
        PAUSED = 'PAUSED', 'Paused'

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student} -> {self.course}"


class CourseProgress(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='course_progress')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='progress_records')
    last_accessed = models.DateTimeField(auto_now=True)
    completion_percentage = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ('student', 'course')


class Quiz(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=200, blank=True)
    passing_score = models.PositiveSmallIntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Quiz #{self.pk}"


class Question(models.Model):
    """
    A standalone question bank (the "Najwa Limited"-style idea from the brief):
    each question is tagged with a topic (category) so the adaptive quiz
    engine can focus on each student's individual weak spots.
    """
    class Difficulty(models.TextChoices):
        EASY = 'EASY', 'Easy'
        MEDIUM = 'MEDIUM', 'Medium'
        HARD = 'HARD', 'Hard'

    topic = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='questions',
        help_text='The topic/category the adaptive engine uses for personalization'
    )
    question_text = models.TextField()
    correct_answer = models.CharField(max_length=255, blank=True)
    difficulty_level = models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM)
    is_ai_generated = models.BooleanField(
        default=False,
        help_text='True for questions generated on-the-fly by Gemini; False for the teacher\'s own question bank.'
    )

    def __str__(self):
        return self.question_text[:50]


class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='quiz_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='quiz_links')
    order_number = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('quiz', 'question')


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.choice_text


class QuizAttempt(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.FloatField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.student} - {self.quiz} - {self.score}"


class UserAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='user_answers')
    selected_choice = models.ForeignKey(Choice, on_delete=models.SET_NULL, null=True, blank=True)
    answer_text = models.CharField(max_length=255, blank=True)
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)


class StudentPerformance(models.Model):
    """
    Summary of a student's performance per topic (updated automatically after
    every quiz attempt). This is what the adaptive engine reads to know
    where each student is weak.
    """
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='topic_performances')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='topic_performances')
    topic = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='performance_records')
    correct_answers = models.PositiveIntegerField(default=0)
    wrong_answers = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('student', 'course', 'topic')

    @property
    def weakness_score(self) -> float:
        total = self.correct_answers + self.wrong_answers
        if total == 0:
            return 0.0
        return self.wrong_answers / total


class StudySession(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='study_sessions')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='study_sessions')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=0)


class StudyPlan(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='study_plans')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='study_plans')
    topic = models.CharField(max_length=200)
    action_items = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.topic}"
