from django.urls import path
from . import views

app_name = 'learning'

urlpatterns = [
    path('', views.course_list_view, name='course_list'),
    path('course/<int:course_id>/', views.course_detail_view, name='course_detail'),
    path('course/<int:course_id>/enroll/', views.enroll_view, name='enroll'),
    path('lesson/<int:lesson_id>/', views.lesson_detail_view, name='lesson_detail'),
    path('lesson/<int:lesson_id>/summarize/', views.lesson_summarize_view, name='lesson_summarize'),
    path('quiz/<int:quiz_id>/', views.quiz_take_view, name='quiz_take'),
    path('quiz/<int:quiz_id>/submit/', views.quiz_submit_view, name='quiz_submit'),
]
