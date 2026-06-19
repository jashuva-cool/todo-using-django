from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Notification, Task


@receiver(post_save, sender=Task)
def create_task_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(user=instance.user, task=instance, message=f"Task created: {instance.title}")
    elif instance.completed:
        Notification.objects.get_or_create(user=instance.user, task=instance, message=f"Task completed: {instance.title}")
    else:
        Notification.objects.get_or_create(user=instance.user, task=instance, message=f"Task pending: {instance.title}")
