import base64
import json
from urllib import parse, request

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Notification, Task


def task_queryset(user):
    return Task.objects.filter(user=user).select_related("category")


def create_task_reminders(user, reminder_window_hours=24):
    """Create unread reminders for pending tasks due soon or already overdue."""
    now = timezone.now()
    soon = now + timezone.timedelta(hours=reminder_window_hours)
    pending_tasks = task_queryset(user).filter(completed=False)
    created_count = 0

    for task in pending_tasks.filter(due_datetime__range=(now, soon)):
        message = f"Reminder: '{task.title}' is still pending and due on {timezone.localtime(task.due_datetime):%b %d, %Y at %I:%M %p}."
        _, created = Notification.objects.get_or_create(
            user=user,
            task=task,
            message=message,
        )
        if created:
            send_external_task_reminders(task, message)
        created_count += int(created)

    for task in pending_tasks.filter(due_datetime__lt=now):
        message = f"Overdue reminder: '{task.title}' is pending and was due on {timezone.localtime(task.due_datetime):%b %d, %Y at %I:%M %p}."
        _, created = Notification.objects.get_or_create(
            user=user,
            task=task,
            message=message,
        )
        if created:
            send_external_task_reminders(task, message)
        created_count += int(created)

    return created_count


def send_pending_task_reminder_email(task):
    if not task.user.email or task.completed:
        return False

    due_at = timezone.localtime(task.due_datetime).strftime("%b %d, %Y at %I:%M %p")
    send_mail(
        subject=f"TaskFlow reminder: {task.title}",
        message=(
            f"Your task '{task.title}' is still pending.\n\n"
            f"Scheduled due time: {due_at}\n"
            "Please open TaskFlow to complete it or update the schedule."
        ),
        from_email=None,
        recipient_list=[task.user.email],
        fail_silently=True,
    )
    return True


def send_external_task_reminders(task, message):
    profile = getattr(task.user, "profile", None)
    if not profile:
        return []

    deliveries = []
    if profile.enable_telegram_reminders and profile.telegram_chat_id:
        deliveries.append(send_telegram_message(profile.telegram_chat_id, message))
    if profile.enable_whatsapp_reminders and profile.whatsapp_number:
        deliveries.append(send_whatsapp_message(profile.whatsapp_number, message))
    return deliveries


def send_telegram_message(chat_id, message):
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": f"TaskFlow\n{message}"}).encode("utf-8")
    req = request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with request.urlopen(req, timeout=10) as response:
            return 200 <= response.status < 300
    except Exception:
        return False


def send_whatsapp_message(number, message):
    sid = settings.TWILIO_ACCOUNT_SID
    token = settings.TWILIO_AUTH_TOKEN
    sender = settings.TWILIO_WHATSAPP_FROM
    if not all([sid, token, sender]):
        return False

    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    auth = base64.b64encode(f"{sid}:{token}".encode("utf-8")).decode("ascii")
    payload = parse.urlencode(
        {
            "From": _whatsapp_address(sender),
            "To": _whatsapp_address(number),
            "Body": f"TaskFlow\n{message}",
        }
    ).encode("utf-8")
    req = request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=10) as response:
            return 200 <= response.status < 300
    except Exception:
        return False


def _whatsapp_address(number):
    return number if number.startswith("whatsapp:") else f"whatsapp:{number}"
