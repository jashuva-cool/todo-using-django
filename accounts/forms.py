from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "avatar",
            "bio",
            "telegram_chat_id",
            "enable_telegram_reminders",
            "whatsapp_number",
            "enable_whatsapp_reminders",
        ]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
            "telegram_chat_id": forms.TextInput(attrs={"placeholder": "Example: 123456789"}),
            "whatsapp_number": forms.TextInput(attrs={"placeholder": "Example: +919876543210"}),
        }
