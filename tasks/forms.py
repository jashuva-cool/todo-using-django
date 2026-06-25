from django import forms
from django.utils import timezone

from .models import Category, Task


class BootstrapFormMixin:
    def apply_bootstrap(self):
        for field in self.fields.values():
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            field.widget.attrs["class"] = f"{field.widget.attrs.get('class', '')} {css_class}".strip()


class TaskForm(BootstrapFormMixin, forms.ModelForm):
    due_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    due_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))
    custom_category = forms.CharField(
        required=False,
        label="Category",
        max_length=80,
        help_text="Type the category name you want for this task.",
        widget=forms.TextInput(attrs={"placeholder": "Example: College, Office, Personal"}),
    )

    class Meta:
        model = Task
        fields = ["title", "description", "priority", "custom_category", "due_date", "due_time", "completed"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if self.instance and self.instance.pk:
            self.fields["due_date"].initial = self.instance.due_datetime.date()
            self.fields["due_time"].initial = self.instance.due_datetime.strftime("%H:%M")
            if self.instance.category:
                self.fields["custom_category"].initial = self.instance.category.name
        self.apply_bootstrap()

    def clean(self):
        cleaned = super().clean()
        due_date = cleaned.get("due_date")
        due_time = cleaned.get("due_time")
        if due_date and due_time:
            cleaned["due_datetime"] = timezone.make_aware(timezone.datetime.combine(due_date, due_time))
        return cleaned

    def save(self, commit=True):
        task = super().save(commit=False)
        task.due_datetime = self.cleaned_data["due_datetime"]
        if self.user:
            task.user = self.user
        custom_category = self.cleaned_data.get("custom_category", "").strip()
        if custom_category and self.user:
            category, _ = Category.objects.get_or_create(
                user=self.user,
                name=custom_category,
                defaults={"color": "#5b8def"},
            )
            task.category = category
        else:
            task.category = None
        if commit:
            task.save()
            self.save_m2m()
        return task


class CategoryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "color"]
        widgets = {"color": forms.TextInput(attrs={"type": "color"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()
