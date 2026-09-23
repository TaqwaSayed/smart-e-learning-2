import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import models
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.translation import get_language, gettext_lazy as _
from django.views.decorators.http import require_POST

from .models import Course, Lesson, Quiz, Enrollment, QuizAttempt, Choice, CourseProgress, LiveLecture
from .services import build_adaptive_quiz, record_quiz_result
from .ai_helpers import summarize_lesson_content
from .forms import CourseForm, LessonForm
from .permissions import can_manage_course, can_manage_courses, instructor_required


@login_required
def lesson_detail_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    is_enrolled = Enrollment.objects.filter(student=request.user, course=lesson.course).exists()
    quizzes = lesson.quizzes.all()
    return render(request, 'learning/lesson_detail.html', {
        'lesson': lesson,
        'is_enrolled': is_enrolled,
        'quizzes': quizzes,
        'can_manage': can_manage_course(request.user, lesson.course),
    })


@login_required
@require_POST
def lesson_summarize_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    summary = summarize_lesson_content(lesson.content, language=get_language())
    if summary is None:
        return JsonResponse({
            'error': _('Summarization is not available right now (check GEMINI_API_KEY in your .env).')
        }, status=503)
    return JsonResponse({'summary': summary})


@login_required
def course_list_view(request):
    courses = Course.objects.select_related('category', 'instructor').all()
    enrolled_ids = set(
        Enrollment.objects.filter(student=request.user).values_list('course_id', flat=True)
    )
    manageable_ids = {c.id for c in courses if can_manage_course(request.user, c)}
    return render(request, 'learning/course_list.html', {
        'courses': courses,
        'enrolled_ids': enrolled_ids,
        'manageable_ids': manageable_ids,
        'can_create_course': can_manage_courses(request.user),
    })


@login_required
def course_detail_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    lessons = course.lessons.all()
    is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    progress = CourseProgress.objects.filter(student=request.user, course=course).first()
    progress_percentage = progress.completion_percentage if progress else 0
    return render(request, 'learning/course_detail.html', {
        'course': course,
        'lessons': lessons,
        'is_enrolled': is_enrolled,
        'progress_percentage': progress_percentage,
        'progress_remaining': 100 - progress_percentage,
        'can_manage': can_manage_course(request.user, course),
    })


@login_required
@instructor_required
def course_create_view(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()

            if hasattr(request.user, 'add_points'):
                request.user.add_points(10, reason=str(_('Created a new course')))

            messages.success(request, _('Course created successfully.'))
            return redirect('learning:course_detail', course_id=course.id)
    else:
        form = CourseForm()
    return render(request, 'learning/course_form.html', {'form': form, 'mode': 'create'})


@login_required
def course_edit_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if not can_manage_course(request.user, course):
        raise PermissionDenied(_("You don't have permission to edit this course."))

    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()

            if hasattr(request.user, 'add_points'):
                request.user.add_points(10, reason=str(_('Updated course content')))

            messages.success(request, _('Course updated successfully.'))
            return redirect('learning:course_detail', course_id=course.id)
    else:
        form = CourseForm(instance=course)
    return render(request, 'learning/course_form.html', {'form': form, 'mode': 'edit', 'course': course})


@login_required
@require_POST
def course_delete_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if not can_manage_course(request.user, course):
        raise PermissionDenied(_("You don't have permission to delete this course."))
    course.delete()
    messages.success(request, _('Course deleted.'))
    return redirect('learning:course_list')


@login_required
def lesson_create_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if not can_manage_course(request.user, course):
        raise PermissionDenied(_("You don't have permission to add lessons to this course."))

    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()

            if hasattr(request.user, 'add_points'):
                request.user.add_points(5, reason=str(_('Added a new lesson')))

            messages.success(request, _('Lesson added.'))
            return redirect('learning:course_detail', course_id=course.id)
    else:
        form = LessonForm(initial={'order_number': course.lessons.count() + 1})
    return render(request, 'learning/lesson_form.html', {'form': form, 'mode': 'create', 'course': course})


@login_required
def lesson_edit_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    if not can_manage_course(request.user, course):
        raise PermissionDenied(_("You don't have permission to edit this lesson."))

    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, _('Lesson updated.'))
            return redirect('learning:lesson_detail', lesson_id=lesson.id)
    else:
        form = LessonForm(instance=lesson)
    return render(request, 'learning/lesson_form.html', {
        'form': form, 'mode': 'edit', 'course': course, 'lesson': lesson,
    })


@login_required
@require_POST
def lesson_delete_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    if not can_manage_course(request.user, course):
        raise PermissionDenied(_("You don't have permission to delete this lesson."))
    lesson.delete()
    messages.success(request, _('Lesson deleted.'))
    return redirect('learning:course_detail', course_id=course.id)


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
    submitted_answers = payload.get('answers', [])

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


@login_required
@instructor_required
def live_lecture_create_view(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        course_id = request.POST.get('course_id')
        scheduled_at = request.POST.get('scheduled_at')
        zoom_url = request.POST.get('zoom_url') or "https://zoom.us/test"

        course = get_object_or_404(Course, pk=course_id)

        LiveLecture.objects.create(
            title=title,
            course=course,
            instructor=request.user,
            scheduled_at=scheduled_at,
            zoom_url=zoom_url
        )

        if hasattr(request.user, 'add_points'):
            request.user.add_points(5, reason=str(_('Scheduled a new live lecture')))

        messages.success(request, _('Live lecture scheduled successfully.'))
        return redirect('core:dashboard')

    courses = Course.objects.filter(instructor=request.user)
    return render(request, 'learning/live_lecture_form.html', {'courses': courses})