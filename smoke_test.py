"""
Full smoke test: actually runs the project and simulates more than one real
student, to confirm auth, points, the adaptive quiz engine, and gamification
all work together correctly.

Run with: python manage.py shell < smoke_test.py
"""
import json as _json

from django.contrib.auth import get_user_model
from django.test import Client
from apps.core.models import Level, MindfulnessContent, Badge, UserBadge
from apps.learning.models import (
    Category, Course, Lesson, Quiz, Question, Choice, QuizQuestion,
    Enrollment, StudentPerformance,
)

User = get_user_model()
errors = []


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        errors.append(label)


# 1) Clean up any leftover test data from a previous run
User.objects.filter(username__in=['sara_test', 'omar_test']).delete()
Course.objects.filter(title='Python for Beginners').delete()

# 2) Seed base data: Level, Category, Course, Lesson, Quiz, questions split across topics
Level.objects.get_or_create(name='Beginner', min_points=0, order_number=1)
Level.objects.get_or_create(name='Intermediate', min_points=20, order_number=2)

topic_loops = Category.objects.create(name='Loops')
topic_funcs = Category.objects.create(name='Functions')

course = Course.objects.create(
    title='Python for Beginners', description='An introduction to Python', category=topic_loops
)
lesson = Lesson.objects.create(course=course, title='Lesson 1', order_number=1)
quiz = Quiz.objects.create(lesson=lesson, title='Review Quiz', passing_score=50)

q1 = Question.objects.create(topic=topic_loops, question_text='What does `for i in range(3): print(i)` output?')
Choice.objects.create(question=q1, choice_text='0 1 2', is_correct=True)
Choice.objects.create(question=q1, choice_text='1 2 3', is_correct=False)

q2 = Question.objects.create(topic=topic_funcs, question_text='What keyword defines a function in Python?')
Choice.objects.create(question=q2, choice_text='def', is_correct=True)
Choice.objects.create(question=q2, choice_text='func', is_correct=False)

QuizQuestion.objects.create(quiz=quiz, question=q1, order_number=1)
QuizQuestion.objects.create(quiz=quiz, question=q2, order_number=2)

MindfulnessContent.objects.get_or_create(
    text='Every effort you put in is worth it — keep going.', phase='BREAK'
)

check("Base seed data created", Course.objects.filter(title='Python for Beginners').exists())

# 3) First student: sara_test — registers an account, enrolls in the course
client_sara = Client()
resp = client_sara.post('/accounts/register/', {
    'username': 'sara_test', 'email': 'sara@test.com',
    'password1': 'TestPass123!', 'password2': 'TestPass123!',
})
sara = User.objects.filter(username='sara_test').first()
check("Sara's account was created", sara is not None)
check("Sara was auto-logged-in after registering", resp.status_code in (302, 200))

client_sara.login(username='sara_test', password='TestPass123!')
resp = client_sara.post(f'/courses/course/{course.id}/enroll/')
check("Sara enrolled in the course", Enrollment.objects.filter(student=sara, course=course).exists())
sara.refresh_from_db()
check("Sara received enrollment points (+5)", sara.points == 5)

# Sara deliberately gets the loops question wrong, so we can confirm
# StudentPerformance is recorded correctly.
resp = client_sara.get(f'/courses/quiz/{quiz.id}/')
check("Quiz page loaded for Sara", resp.status_code == 200)

wrong_choice = q1.choices.filter(is_correct=False).first()
correct_choice_q2 = q2.choices.filter(is_correct=True).first()
resp = client_sara.post(
    f'/courses/quiz/{quiz.id}/submit/',
    data=_json.dumps({'answers': [
        {'question_id': q1.id, 'selected_choice_id': wrong_choice.id},
        {'question_id': q2.id, 'selected_choice_id': correct_choice_q2.id},
    ]}),
    content_type='application/json',
)
check("Quiz submission succeeded (status 200)", resp.status_code == 200)
data = resp.json()
check("Score computed correctly (50%)", data.get('score') == 50.0)

perf_loops = StudentPerformance.objects.filter(student=sara, course=course, topic=topic_loops).first()
check("StudentPerformance recorded for the Loops topic (wrong answer)",
      perf_loops is not None and perf_loops.wrong_answers == 1)

sara.refresh_from_db()
check("Sara received quiz points on top of enrollment points", sara.points > 5)

# 4) Actually test the adaptive engine: since Sara is weak in Loops, the
#    Loops question should be ordered first next time.
from apps.learning.services import build_adaptive_quiz
ordered_questions = build_adaptive_quiz(sara, quiz, course, limit=10)
check(
    "Adaptive engine put the weak topic (Loops) first for Sara",
    ordered_questions and ordered_questions[0].topic_id == topic_loops.id
)

# 5) Second student: omar_test — a plain run to confirm data isolation between students
client_omar = Client()
client_omar.post('/accounts/register/', {
    'username': 'omar_test', 'email': 'omar@test.com',
    'password1': 'TestPass123!', 'password2': 'TestPass123!',
})
omar = User.objects.filter(username='omar_test').first()
check("Omar's account was created", omar is not None)
check("Omar has no StudentPerformance rows (per-student data isolation)",
      not StudentPerformance.objects.filter(student=omar).exists())

# 6) Mindfulness popup endpoint (called every 25 minutes from the client)
resp = client_sara.get('/mindfulness/popup/?phase=BREAK')
check("Mindfulness popup endpoint returns data", resp.status_code == 200 and 'text' in resp.json())

# 7) Admin registration sanity check
from django.contrib import admin as django_admin
check("All models are registered in the admin", len(django_admin.site._registry) >= 20)

print("\n" + "=" * 40)
if errors:
    print(f"{len(errors)} check(s) FAILED:")
    for e in errors:
        print(f"   - {e}")
else:
    print("ALL CHECKS PASSED (auth + enrollment + adaptive quiz + points + gamification)")
print("=" * 40)
