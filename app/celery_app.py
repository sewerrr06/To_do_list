import smtplib
import ssl
import os
from email.message import EmailMessage

import asyncio
from celery import Celery
from celery.schedules import crontab
from .database import AsyncSessionLocal
from .crud import (
    get_task,
    get_tasks_due_for_overdue_notification,
    mark_task_completed_notified,
    mark_task_overdue_notified,
)
from .models import TaskStatus
from datetime import datetime, timezone

celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.beat_schedule = {
    "notify-overdue-tasks-every-minute": {
        "task": "app.celery_app.send_overdue_deadline_notifications",
        "schedule": crontab(minute='*'),
    },
}
celery_app.conf.timezone = "UTC"


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _send_email(recipient: str, subject: str, body: str):
    smtp_host = os.getenv("SMTP_HOST", "localhost")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM") or smtp_user or "no-reply@localhost"
    smtp_use_tls = _bool_env("SMTP_USE_TLS", True)

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = smtp_from
    message["To"] = recipient
    message.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as smtp:
        if smtp_use_tls:
            smtp.starttls(context=ssl.create_default_context())
        if smtp_user and smtp_password:
            smtp.login(smtp_user, smtp_password)
        smtp.send_message(message)


@celery_app.task
def send_task_completed_email(task_id: int):
    async def run_send_completed_notification():
        async with AsyncSessionLocal() as db:
            task = await get_task(db=db, task_id=task_id)
            if task is None:
                return
            if task.status != TaskStatus.COMPLETED:
                return
            if not task.notification_email:
                return
            if task.completed_notified_at is not None:
                return

            _send_email(
                recipient=task.notification_email,
                subject=f"Завдання виконано: {task.title}",
                body=(
                    f"Завдання '{task.title}' позначено як виконане.\n"
                    f"ID: {task.id}\n"
                    f"Дата завершення: {datetime.now(timezone.utc).isoformat()}"
                ),
            )
            await mark_task_completed_notified(db=db, task=task)

    asyncio.run(run_send_completed_notification())


@celery_app.task
def send_overdue_deadline_notifications():
    async def run_send_overdue_notifications():
        now = datetime.now(timezone.utc)
        async with AsyncSessionLocal() as db:
            tasks = await get_tasks_due_for_overdue_notification(db=db, now=now)
            for task in tasks:
                _send_email(
                    recipient=task.notification_email,
                    subject=f"Пропущено дедлайн: {task.title}",
                    body=(
                        f"У завдання '{task.title}' пропущено дедлайн.\n"
                        f"ID: {task.id}\n"
                        f"Дедлайн: {task.due_date.isoformat() if task.due_date else 'N/A'}"
                    ),
                )
                await mark_task_overdue_notified(db=db, task=task)

    asyncio.run(run_send_overdue_notifications())