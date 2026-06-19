from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="enable_telegram_reminders",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="profile",
            name="enable_whatsapp_reminders",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="profile",
            name="telegram_chat_id",
            field=models.CharField(blank=True, help_text="Telegram chat ID for reminder messages.", max_length=64),
        ),
        migrations.AddField(
            model_name="profile",
            name="whatsapp_number",
            field=models.CharField(blank=True, help_text="WhatsApp number with country code, for example +919876543210.", max_length=20),
        ),
    ]
