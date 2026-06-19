from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from tasks.models import Task
from tasks.services import create_task_reminders, send_external_task_reminders, send_pending_task_reminder_email


class Command(BaseCommand):
    help = "Create and email reminders for pending tasks that are due soon or overdue."

    def add_arguments(self, parser):
        parser.add_argument(
            "--hours",
            type=int,
            default=24,
            help="Reminder window for upcoming pending tasks.",
        )
        parser.add_argument(
            "--email",
            action="store_true",
            help="Also send reminder emails to users with email addresses.",
        )
        parser.add_argument(
            "--external",
            action="store_true",
            help="Also send Telegram and WhatsApp reminders for configured profiles.",
        )

    def handle(self, *args, **options):
        hours = options["hours"]
        now = timezone.now()
        soon = now + timezone.timedelta(hours=hours)
        users = get_user_model().objects.filter(tasks__completed=False).distinct()

        notification_count = 0
        email_count = 0
        external_count = 0
        for user in users:
            notification_count += create_task_reminders(user, reminder_window_hours=hours)
            if options["email"] or options["external"]:
                pending_tasks = Task.objects.filter(
                    user=user,
                    completed=False,
                    due_datetime__lte=soon,
                )
                for task in pending_tasks:
                    if options["email"]:
                        email_count += int(send_pending_task_reminder_email(task))
                    if options["external"]:
                        message = f"Reminder: '{task.title}' is pending and due on {timezone.localtime(task.due_datetime):%b %d, %Y at %I:%M %p}."
                        external_count += sum(1 for delivered in send_external_task_reminders(task, message) if delivered)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {notification_count} reminder notifications, sent {email_count} emails, and delivered {external_count} external messages."
            )
        )
