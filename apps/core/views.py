import random

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.translation import get_language
from django.views.decorators.http import require_POST

from .models import MindfulnessContent, UserBadge, Goal, Points, StudentTask
from apps.learning.models import Enrollment, CourseProgress


@login_required
def dashboard_view(request):
    user = request.user
    recent_points = Points.objects.filter(student=user).order_by('-created_at')[:5]
    badges = UserBadge.objects.filter(student=user).select_related('badge')
    today_goal = Goal.objects.filter(student=user, goal_date=timezone.localdate()).first()
    tasks = StudentTask.objects.filter(student=user)

    # Courses the student is enrolled in, each annotated with its progress
    # percentage (for the red -> green progress bar in the template).
    my_courses = (
        Enrollment.objects.filter(student=user)
        .select_related('course', 'course__category', 'course__instructor')
        .order_by('-enrolled_at')
    )
    progress_map = {
        cp.course_id: cp.completion_percentage
        for cp in CourseProgress.objects.filter(student=user)
    }
    for enrollment in my_courses:
        enrollment.progress_percentage = progress_map.get(enrollment.course_id, 0)
        enrollment.progress_remaining = 100 - enrollment.progress_percentage

    # A rotating azkar/dhikr quote for the dashboard's "Azkar" card.
    # Dashboard Azkar card shows general reminders (BREAK phase) — the
    # BEFORE/AFTER ones are reserved for the lesson-start/quiz-end popups.
    azkar_item = MindfulnessContent.objects.filter(phase=MindfulnessContent.Phase.DURING_BREAK).order_by('?').first()

    context = {
        'recent_points': recent_points,
        'badges': badges,
        'today_goal': today_goal,
        'my_courses': my_courses,
        'tasks': tasks,
        'azkar_item': azkar_item,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
@require_POST
def task_create_view(request):
    text = request.POST.get('text', '').strip()
    is_ajax = request.headers.get('X-Requested-With') == 'fetch'

    if not text:
        if is_ajax:
            return JsonResponse({'error': 'Task text is empty'}, status=400)
        return redirect('core:dashboard')

    task = StudentTask.objects.create(student=request.user, text=text)
    if is_ajax:
        return JsonResponse({'id': task.id, 'text': task.text, 'is_done': task.is_done})
    return redirect('core:dashboard')


@login_required
@require_POST
def task_toggle_view(request, task_id):
    task = get_object_or_404(StudentTask, id=task_id, student=request.user)
    task.is_done = not task.is_done
    task.completed_at = timezone.now() if task.is_done else None
    task.save(update_fields=['is_done', 'completed_at'])
    if task.is_done:
        request.user.add_points(2, reason=f'Completed task: {task.text}')

    if request.headers.get('X-Requested-With') == 'fetch':
        request.user.refresh_from_db()
        return JsonResponse({'id': task.id, 'is_done': task.is_done, 'points': request.user.points})
    return redirect('core:dashboard')


@login_required
def mindfulness_popup(request):
    """
    Called from the JS every 25 minutes (Pomodoro-style), and once when
    starting/finishing a lesson or quiz, to fetch a reminder / verse / dua —
    as an image (if one was uploaded in the admin) and/or text.
    GET param: phase = BEFORE | BREAK | AFTER
    """
    phase = request.GET.get('phase', MindfulnessContent.Phase.DURING_BREAK)
    items = list(MindfulnessContent.objects.filter(phase=phase))
    if not items:
        if get_language() == 'ar':
            return JsonResponse({'text': 'سبحان الله وبحمده، سبحان الله العظيم', 'source': 'ذكر'})
        return JsonResponse({'text': 'Take a breath — small consistent effort beats burnout.', 'source': 'Reminder'})

    item = random.choice(items)
    image_url = item.image.url if item.image else None
    return JsonResponse({'text': item.text, 'source': item.source or 'Reminder', 'image_url': image_url})
