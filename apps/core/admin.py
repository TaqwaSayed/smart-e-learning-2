from django.contrib import admin
from .models import (
    MindfulnessContent, Badge, UserBadge, Goal,
    DhikrContent, DhikrCompletion, Points, Level, StudentTask,
    AIChatSession, AIMessage,
)

admin.site.register(MindfulnessContent)
admin.site.register(Badge)
admin.site.register(UserBadge)
admin.site.register(Goal)
admin.site.register(DhikrContent)
admin.site.register(DhikrCompletion)
admin.site.register(Points)
admin.site.register(Level)
admin.site.register(StudentTask)
admin.site.register(AIChatSession)
admin.site.register(AIMessage)
