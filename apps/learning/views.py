import json

from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.translation import get_language
from django.views.decorators.http import require_POST

from .models import Course, Lesson, Quiz, Enrollment, QuizAttempt, Choice, CourseProgress
from .services import build_adaptive_quiz, record_quiz_result
from .ai_helpers import summarize_lesson_content


@login_required
def lesson_detail_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    is_enrolled = Enrollment.objects.filter(student=request.user, course=lesson.course).exists()
    quizzes = lesson.quizzes.all()
    return render(request, 'learning/lesson_detail.html', {
        'lesson': lesson, 'is_enrolled': is_enrolled, 'quizzes': quizzes,
    })


@login_required
@require_POST
def lesson_summarize_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    summary = summarize_lesson_content(lesson.content, language=get_language())
    if summary is None:
        return JsonResponse({
            'error': 'Summarization is not available right now (check GEMINI_API_KEY in your .env).'
        }, status=503)
    return JsonResponse({'summary': summary})


@login_required
def course_list_view(request):
    courses = Course.objects.select_related('category').all()
    enrolled_ids = set(
        Enrollment.objects.filter(student=request.user).values_list('course_id', flat=True)
    )
    return render(request, 'learning/course_list.html', {
        'courses': courses, 'enrolled_ids': enrolled_ids,
    })


@login_required
def course_detail_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    lessons = course.lessons.all()
    is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    progress = CourseProgress.objects.filter(student=request.user, course=course).first()
    progress_percentage = progress.completion_percentage if progress else 0
    return render(request, 'learning/course_detail.html', {
        'course': course, 'lessons': lessons, 'is_enrolled': is_enrolled,
        'progress_percentage': progress_percentage,
        'progress_remaining': 100 - progress_percentage,
    })


@login_required
@require_POST
def enroll_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    Enrollment.objects.get_or_create(student=request.user, course=course)
    request.user.add_points(5, reason=f'Enrolled in course: {course.title}')
    return redirect('learning:course_detail', course_id=course.id)


@login_required
def quiz_take_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    course = quiz.lesson.course
    questions = build_adaptive_quiz(request.user, quiz, course, limit=10)
    return render(request, 'learning/quiz_take.html', {
        'quiz': quiz, 'questions': questions,
    })


def _update_course_progress(student, course):
    """
    Progress = share of the course's quizzes the student has passed.
    Recomputed after every quiz submission and stored on CourseProgress,
    which the dashboard/course page turn into the red-to-green bar.
    """
    total_quizzes = Quiz.objects.filter(lesson__course=course).count()
    if total_quizzes == 0:
        return
    passed_quiz_ids = set(
        QuizAttempt.objects.filter(student=student, quiz__lesson__course=course)
        .filter(score__gte=models.F('quiz__passing_score'))
        .values_list('quiz_id', flat=True)
    )
    percentage = min(100, round((len(passed_quiz_ids) / total_quizzes) * 100))
    CourseProgress.objects.update_or_create(
        student=student, course=course,
        defaults={'completion_percentage': percentage},
    )


@login_required
@require_POST
def quiz_submit_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    course = quiz.lesson.course
    payload = json.loads(request.body or '{}')
    submitted_answers = payload.get('answers', [])  # [{question_id, selected_choice_id}]

    attempt = QuizAttempt.objects.create(student=request.user, quiz=quiz)

    answers_data = []
    for ans in submitted_answers:
        choice_id = ans.get('selected_choice_id')
        is_correct = False
        if choice_id:
            is_correct = Choice.objects.filter(id=choice_id, is_correct=True).exists()
        answers_data.append({
            'question_id': ans['question_id'],
            'selected_choice_id': choice_id,
            'is_correct': is_correct,
        })

    score = record_quiz_result(attempt, answers_data)
    attempt.score = score
    attempt.completed_at = timezone.now()
    attempt.save(update_fields=['score', 'completed_at'])

    points_earned = 10 if score >= quiz.passing_score else 2
    request.user.add_points(points_earned, reason=f'Quiz {quiz} - score {score}%')
    _update_course_progress(request.user, course)

    return JsonResponse({'score': score, 'points_earned': points_earned})
