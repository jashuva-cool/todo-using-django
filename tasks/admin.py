from django.contrib import admin
from django.db.models import Count, Q

from .models import Category, Notification, Task


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "color", "created_at")
    search_fields = ("name", "user__username")
    list_filter = ("created_at",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "category", "priority", "status", "completed", "due_datetime")
    search_fields = ("title", "description", "user__username", "category__name")
    list_filter = ("priority", "status", "completed", "category", "due_datetime")
    date_hierarchy = "due_datetime"

    def changelist_view(self, request, extra_context=None):
        stats = Task.objects.aggregate(
            total=Count("id"),
            completed=Count("id", filter=Q(completed=True)),
            pending=Count("id", filter=Q(completed=False)),
        )
        extra_context = extra_context or {}
        extra_context["task_stats"] = stats
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("message", "user", "is_read", "created_at")
    search_fields = ("message", "user__username")
    list_filter = ("is_read", "created_at")
