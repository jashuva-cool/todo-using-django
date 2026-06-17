# TaskFlow

TaskFlow is a full-stack Django 5 To-Do Management Web Application with user accounts, profiles, task scheduling, categories, notifications, calendar views, CSV export, responsive Bootstrap 5 UI, dark mode, and AJAX task completion.

## Tech Stack

- Python 3.12
- Django 5+
- SQLite
- Bootstrap 5
- Bootstrap Icons
- HTML, CSS, JavaScript
- Django Authentication System

## Setup

```bash
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Deploy on Render

1. Push this project to GitHub.
2. Create a new Render Web Service from the GitHub repository.
3. Use:
   - Build command: `./build.sh`
   - Start command: `gunicorn taskflow.wsgi:application`
4. Add environment variables:
   - `DEBUG=False`
   - `SECRET_KEY=<generate a secure value>`
   - `ALLOWED_HOSTS=<your-render-domain>`
   - `CSRF_TRUSTED_ORIGINS=https://<your-render-domain>`

The included `render.yaml` can also be used as a Render blueprint.

## Features

- Registration, login, logout, password reset, profile page, profile editing, avatar upload
- Create, edit, delete, view, complete, and reopen tasks
- User-owned categories with color labels
- Dashboard metrics for total, completed, pending, and overdue tasks
- Recent tasks, upcoming tasks, overdue tasks
- Search, category filter, priority filter, status filter, due date sorting
- Notification model, notification bell, unread count, due and overdue task alerts
- Monthly calendar, tasks by date, upcoming and overdue lists
- CSV export
- Pagination
- Console email backend for local password resets and reminders
- Custom admin search, filters, and task statistics

## Notes

The default email backend prints password reset and reminder emails to the console for local development. Replace the email settings in `taskflow/settings.py` when deploying.

For production, move secrets into environment variables, set `DEBUG = False`, configure `ALLOWED_HOSTS`, use a production database, configure static/media hosting, and enable HTTPS security settings.
