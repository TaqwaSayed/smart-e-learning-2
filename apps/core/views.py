import json
import random

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.translation import get_language, gettext_lazy as _
from django.views.decorators.http import require_POST

from .models import MindfulnessContent, UserBadge, Goal, Points, StudentTask, AIChatSession, AIMessage
from .ai_chat import run_agentic_chat, sanitize_user_message
from apps.learning.models import Course, Enrollment, LiveLecture, CourseProgress


@login_required
def dashboard_view(request):
    user = request.user
    show_azkar = not user.is_staff  # إخفاء الأذكار تماماً إذا كان المستخدم is_staff

    if user.is_staff:
        if not StudentTask.objects.filter(student=user).exists():
            default_tasks = [
                _("Lecture 1 - 07:00 AM"),
                _("Lecture 2 - 09:00 AM"),
                _("Review assignments - 11:00 AM"),
                _("Update course contents"),
                _("Add Zoom link for upcoming lecture")
            ]
            for task_text in default_tasks:
                StudentTask.objects.create(student=user, text=str(task_text))

        my_courses = Course.objects.filter(instructor=user).select_related('category').order_by('-created_at')
        upcoming_lectures = LiveLecture.objects.filter(
            instructor=user,
            scheduled_at__gte=timezone.now()
        ).select_related('course').order_by('scheduled_at')
        tasks = StudentTask.objects.filter(student=user)

        context = {
            'my_courses': my_courses,
            'upcoming_lectures': upcoming_lectures,
            'tasks': tasks,
            'show_azkar': False,
        }
    else:
        recent_points = Points.objects.filter(student=user).order_by('-created_at')[:5]
        badges = UserBadge.objects.filter(student=user).select_related('badge')
        today_goal = Goal.objects.filter(student=user, goal_date=timezone.localdate()).first()
        tasks = StudentTask.objects.filter(student=user)

        enrollments = (
            Enrollment.objects.filter(student=user)
            .select_related('course', 'course__category', 'course__instructor')
            .order_by('-enrolled_at')
        )
        progress_map = {
            cp.course_id: cp.completion_percentage
            for cp in CourseProgress.objects.filter(student=user)
        }

        enrolled_courses = []
        for enrollment in enrollments:
            course = enrollment.course
            course.progress_percentage = progress_map.get(course.id, 0)
            course.progress_remaining = 100 - course.progress_percentage
            enrolled_courses.append(course)

        azkar_gallery = [
            item for item in
            MindfulnessContent.objects.filter(phase=MindfulnessContent.Phase.DURING_BREAK)
            .exclude(image='')
            .exclude(image__isnull=True)
            .order_by('id')
            if item.image
        ]
        azkar_item = None if azkar_gallery else (
            MindfulnessContent.objects.filter(phase=MindfulnessContent.Phase.DURING_BREAK).order_by('?').first()
        )

        context = {
            'recent_points': recent_points,
            'badges': badges,
            'today_goal': today_goal,
            'my_courses': enrolled_courses,
            'tasks': tasks,
            'azkar_gallery': azkar_gallery,
            'azkar_item': azkar_item,
            'show_azkar': show_azkar,
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

    if task.is_done and hasattr(request.user, 'add_points'):
        request.user.add_points(2, reason=f'Completed task: {task.text}')

    if request.headers.get('X-Requested-With') == 'fetch':
        request.user.refresh_from_db()
        points = getattr(request.user, 'points', 0)
        return JsonResponse({'id': task.id, 'is_done': task.is_done, 'points': points})
    return redirect('core:dashboard')


@login_required
def mindfulness_popup(request):
    # إذا كان المستخدم موظف/محاضر لا يتم إرجاع محتوى
    if request.user.is_staff:
        return JsonResponse({'text': '', 'source': '', 'image_url': None})

    phase = request.GET.get('phase', MindfulnessContent.Phase.DURING_BREAK)
    items = list(MindfulnessContent.objects.filter(phase=phase))
    if not items:
        return JsonResponse({'text': '', 'source': '', 'image_url': None})

    item = random.choice(items)
    image_url = item.image.url if item.image else None
    return JsonResponse({'text': item.text or '', 'source': item.source or '', 'image_url': image_url})


@login_required
def chat_view(request):
    return render(request, 'core/chat.html')


@login_required
@require_POST
def chat_send_view(request):
    payload = json.loads(request.body or '{}')
    user_message = sanitize_user_message(payload.get('message', ''))
    course_id = payload.get('course_id')
    session_id = payload.get('session_id')

    if not user_message:
        return JsonResponse({'error': 'Message is empty'}, status=400)

    session = None
    if session_id:
        session = AIChatSession.objects.filter(id=session_id, student=request.user).first()
    if not session:
        session = AIChatSession.objects.create(student=request.user, course_id=course_id)

    history = [
        {"role": "user" if m.sender == AIMessage.Sender.USER else "assistant", "content": m.message_text}
        for m in session.messages.order_by('created_at')
    ]

    AIMessage.objects.create(session=session, sender=AIMessage.Sender.USER, message_text=user_message)

    reply_text = run_agentic_chat(
        student=request.user,
        message=user_message,
        course=session.course,
        history=history,
        language=get_language(),
    )

    AIMessage.objects.create(session=session, sender=AIMessage.Sender.AI, message_text=reply_text)

    return JsonResponse({'reply': reply_text, 'session_id': session.id})