from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Fields', {'fields': ('role', 'points', 'study_streak', 'level', 'preferred_language')}),
    )
    list_display = ['username', 'email', 'role', 'points', 'level', 'study_streak', 'is_staff']
