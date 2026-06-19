from .services import create_task_reminders


def notifications(request):
    if not request.user.is_authenticated:
        return {"unread_notifications_count": 0, "recent_notifications": []}
    create_task_reminders(request.user)
    qs = request.user.notifications.all()
    return {
        "unread_notifications_count": qs.filter(is_read=False).count(),
        "recent_notifications": qs[:5],
    }
