from django.urls import path
from . import views

app_name = 'learning'

urlpatterns = [
    path('', views.course_list_view, name='course_list'),
    path('new/', views.course_create_view, name='course_create'),
    path('course/<int:course_id>/', views.course_detail_view, name='course_detail'),
    path('course/<int:course_id>/edit/', views.course_edit_view, name='course_edit'),
    path('course/<int:course_id>/delete/', views.course_delete_view, name='course_delete'),
    path('course/<int:course_id>/enroll/', views.enroll_view, name='enroll'),
    path('course/<int:course_id>/lesson/new/', views.lesson_create_view, name='lesson_create'),
    path('lesson/<int:lesson_id>/', views.lesson_detail_view, name='lesson_detail'),
    path('lesson/<int:lesson_id>/edit/', views.lesson_edit_view, name='lesson_edit'),
    path('lesson/<int:lesson_id>/delete/', views.lesson_delete_view, name='lesson_delete'),
    path('lesson/<int:lesson_id>/summarize/', views.lesson_summarize_view, name='lesson_summarize'),
    path('quiz/<int:quiz_id>/', views.quiz_take_view, name='quiz_take'),
    path('quiz/<int:quiz_id>/submit/', views.quiz_submit_view, name='quiz_submit'),
    path('lecture/new/', views.live_lecture_create_view, name='live_lecture_create'),
]