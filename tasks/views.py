import calendar
import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CategoryForm, TaskForm
from .models import Category, Notification, Task


def task_queryset(user):
    return Task.objects.filter(user=user).select_related("category")


@login_required
def dashboard(request):
    now = timezone.now()
    tasks = task_queryset(request.user)
    pending_tasks = tasks.filter(completed=False)
    context = {
        "total_tasks": tasks.count(),
        "completed_tasks": tasks.filter(completed=True).count(),
        "pending_tasks": pending_tasks.count(),
        "overdue_tasks": pending_tasks.filter(due_datetime__lt=now).count(),
        "recent_tasks": tasks.order_by("-created_at")[:5],
        "upcoming_tasks": pending_tasks.filter(due_datetime__gte=now).order_by("due_datetime")[:6],
        "overdue_list": pending_tasks.filter(due_datetime__lt=now).order_by("due_datetime")[:6],
    }
    create_due_notifications(request.user)
    return render(request, "tasks/dashboard.html", context)


@login_required
def task_list(request):
    tasks = task_queryset(request.user)
    categories = Category.objects.filter(user=request.user)
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category")
    priority = request.GET.get("priority")
    status = request.GET.get("status")
    sort = request.GET.get("sort", "due")

    if query:
        tasks = tasks.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if category:
        tasks = tasks.filter(category_id=category)
    if priority:
        tasks = tasks.filter(priority=priority)
    if status == "completed":
        tasks = tasks.filter(completed=True)
    elif status == "pending":
        tasks = tasks.filter(completed=False)

    sort_map = {
        "due": "due_datetime",
        "due_desc": "-due_datetime",
        "created": "-created_at",
        "priority": "-priority",
    }
    tasks = tasks.order_by(sort_map.get(sort, "due_datetime"))
    paginator = Paginator(tasks, 8)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "tasks/task_list.html",
        {
            "page_obj": page_obj,
            "categories": categories,
            "priorities": Task.PRIORITY_CHOICES,
            "filters": request.GET,
        },
    )


@login_required
def task_detail(request, pk):
    task = get_object_or_404(task_queryset(request.user), pk=pk)
    return render(request, "tasks/task_detail.html", {"task": task})


@login_required
def task_create(request):
    form = TaskForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        task = form.save()
        maybe_send_reminder_email(task)
        messages.success(request, "Task created successfully.")
        return redirect(task)
    return render(request, "tasks/task_form.html", {"form": form, "title": "Create Task"})


@login_required
def task_update(request, pk):
    task = get_object_or_404(task_queryset(request.user), pk=pk)
    form = TaskForm(request.POST or None, user=request.user, instance=task)
    if request.method == "POST" and form.is_valid():
        task = form.save()
        maybe_send_reminder_email(task)
        messages.success(request, "Task updated successfully.")
        return redirect(task)
    return render(request, "tasks/task_form.html", {"form": form, "title": "Edit Task"})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(task_queryset(request.user), pk=pk)
    if request.method == "POST":
        task.delete()
        messages.success(request, "Task deleted.")
        return redirect("task_list")
    return render(request, "tasks/confirm_delete.html", {"object": task, "type": "task"})


@login_required
@require_POST
def toggle_task(request, pk):
    task = get_object_or_404(task_queryset(request.user), pk=pk)
    completed = request.POST.get("completed")
    task.completed = completed == "true" if completed is not None else not task.completed
    task.save()
    if task.completed:
        Notification.objects.get_or_create(user=request.user, task=task, message=f"Task completed: {task.title}")
    return JsonResponse({"ok": True, "completed": task.completed, "status": task.get_status_display()})


@login_required
def category_list(request):
    categories = Category.objects.filter(user=request.user).prefetch_related("tasks")
    return render(request, "tasks/category_list.html", {"categories": categories})


@login_required
def category_create(request):
    form = CategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        category = form.save(commit=False)
        category.user = request.user
        category.save()
        messages.success(request, "Category added.")
        return redirect("category_list")
    return render(request, "tasks/category_form.html", {"form": form, "title": "Add Category"})


@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category updated.")
        return redirect("category_list")
    return render(request, "tasks/category_form.html", {"form": form, "title": "Edit Category"})


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted.")
        return redirect("category_list")
    return render(request, "tasks/confirm_delete.html", {"object": category, "type": "category"})


@login_required
def notifications_view(request):
    notifications = request.user.notifications.all()
    if request.method == "POST":
        notifications.update(is_read=True)
        messages.success(request, "Notifications marked as read.")
        return redirect("notifications")
    return render(request, "tasks/notifications.html", {"notifications": notifications})


@login_required
def calendar_view(request):
    today = timezone.localdate()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))
    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdatescalendar(year, month)
    start = weeks[0][0]
    end = weeks[-1][-1]
    tasks = task_queryset(request.user).filter(due_datetime__date__range=(start, end))
    tasks_by_date = {}
    for task in tasks:
        tasks_by_date.setdefault(task.due_datetime.date(), []).append(task)
    prev_month = month - 1 or 12
    prev_year = year - 1 if month == 1 else year
    next_month = month + 1 if month < 12 else 1
    next_year = year + 1 if month == 12 else year
    return render(
        request,
        "tasks/calendar.html",
        {
            "weeks": weeks,
            "tasks_by_date": tasks_by_date,
            "month_name": calendar.month_name[month],
            "year": year,
            "month": month,
            "today": today,
            "prev_year": prev_year,
            "prev_month": prev_month,
            "next_year": next_year,
            "next_month": next_month,
            "upcoming_tasks": task_queryset(request.user).filter(completed=False, due_datetime__gte=timezone.now())[:8],
            "overdue_tasks": task_queryset(request.user).filter(completed=False, due_datetime__lt=timezone.now())[:8],
        },
    )


@login_required
def export_tasks_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="taskflow_tasks.csv"'
    writer = csv.writer(response)
    writer.writerow(["Title", "Description", "Priority", "Category", "Due DateTime", "Status", "Created At"])
    for task in task_queryset(request.user):
        writer.writerow([
            task.title,
            task.description,
            task.get_priority_display(),
            task.category.name if task.category else "",
            task.due_datetime,
            task.get_status_display(),
            task.created_at,
        ])
    return response


def create_due_notifications(user):
    now = timezone.now()
    soon = now + timezone.timedelta(hours=24)
    for task in task_queryset(user).filter(completed=False, due_datetime__range=(now, soon)):
        Notification.objects.get_or_create(user=user, task=task, message=f"Reminder: {task.title} is due soon.")
    for task in task_queryset(user).filter(completed=False, due_datetime__lt=now):
        Notification.objects.get_or_create(user=user, task=task, message=f"Overdue: {task.title} needs attention.")


def maybe_send_reminder_email(task):
    if task.user.email:
        send_mail(
            subject=f"TaskFlow reminder: {task.title}",
            message=f"Your task is scheduled for {timezone.localtime(task.due_datetime):%Y-%m-%d %H:%M}.",
            from_email=None,
            recipient_list=[task.user.email],
            fail_silently=True,
        )
