from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('mindfulness/popup/', views.mindfulness_popup, name='mindfulness_popup'),
    path('tasks/create/', views.task_create_view, name='task_create'),
    path('tasks/<int:task_id>/toggle/', views.task_toggle_view, name='task_toggle'),
]
