from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    avatar = models.FileField(
        upload_to="profile_pictures/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "gif", "webp"])],
    )
    bio = models.TextField(blank=True)
    telegram_chat_id = models.CharField(
        max_length=64,
        blank=True,
        help_text="Telegram chat ID for reminder messages.",
    )
    whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="WhatsApp number with country code, for example +919876543210.",
    )
    enable_telegram_reminders = models.BooleanField(default=False)
    enable_whatsapp_reminders = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} profile"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        Profile.objects.get_or_create(user=instance)
        instance.profile.save()
