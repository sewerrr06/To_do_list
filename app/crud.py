from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import models, schemas
from datetime import datetime, timezone
from typing import Any


def _normalize_value(value: Any):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, models.TaskStatus):
        return value.value
    return value


def _task_snapshot(task: models.Task) -> dict[str, Any]:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": _normalize_value(task.status),
        "due_date": _normalize_value(task.due_date),
        "created_at": _normalize_value(task.created_at),
        "notification_email": task.notification_email,
        "completed_notified_at": _normalize_value(task.completed_notified_at),
        "overdue_notified_at": _normalize_value(task.overdue_notified_at),
    }


async def _add_task_history(
    db: AsyncSession,
    task_id: int,
    event_type: models.TaskEventType,
    before_data: dict[str, Any] | None,
    after_data: dict[str, Any] | None,
    changed_fields: list[str] | None,
):
    history = models.TaskHistory(
        task_id=task_id,
        event_type=event_type,
        before_data=before_data,
        after_data=after_data,
        changed_fields=changed_fields,
    )
    db.add(history)

async def create_task(db: AsyncSession, task: schemas.TaskCreate):
    db_task = models.Task(**task.model_dump())
    db.add(db_task)
    await db.flush()
    after_data = _task_snapshot(db_task)
    await _add_task_history(
        db=db,
        task_id=db_task.id,
        event_type=models.TaskEventType.CREATED,
        before_data=None,
        after_data=after_data,
        changed_fields=list(after_data.keys()),
    )
    await db.commit()
    await db.refresh(db_task)
    return db_task

async def get_tasks(db: AsyncSession, skip: int = 0, limit: int = 10, status: models.TaskStatus = None):
    query = select(models.Task).offset(skip).limit(limit)

    if status:
        query = query.filter(models.Task.status == status)

    result = await db.execute(query)
    return result.scalars().all()

async def get_task(db: AsyncSession, task_id: int):
    query = select(models.Task).filter(models.Task.id == task_id)
    result = await db.execute(query)
    return result.scalars().first()

async def update_task(db: AsyncSession, task_id: int, task_update: schemas.TaskUpdate):
    db_task = await get_task(db, task_id)
    if not db_task:
        return None

    before_data = _task_snapshot(db_task)
    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)

    after_data = _task_snapshot(db_task)
    changed_fields = [
        field for field in after_data.keys() if before_data.get(field) != after_data.get(field)
    ]

    if changed_fields:
        event_type = models.TaskEventType.UPDATED
        if "status" in changed_fields:
            event_type = models.TaskEventType.STATUS_CHANGED
        await _add_task_history(
            db=db,
            task_id=db_task.id,
            event_type=event_type,
            before_data=before_data,
            after_data=after_data,
            changed_fields=changed_fields,
        )

    await db.commit()
    await db.refresh(db_task)
    return db_task

async def delete_task(db: AsyncSession, task_id: int):
    db_task = await get_task(db, task_id)
    if db_task:
        before_data = _task_snapshot(db_task)
        await _add_task_history(
            db=db,
            task_id=db_task.id,
            event_type=models.TaskEventType.DELETED,
            before_data=before_data,
            after_data=None,
            changed_fields=list(before_data.keys()),
        )
        await db.delete(db_task)
        await db.commit()
        return True
    return False


async def get_task_history(
    db: AsyncSession,
    task_id: int,
    skip: int = 0,
    limit: int = 50,
    event_type: models.TaskEventType | None = None,
):
    query = select(models.TaskHistory).where(models.TaskHistory.task_id == task_id)
    if event_type:
        query = query.where(models.TaskHistory.event_type == event_type)

    query = query.order_by(models.TaskHistory.changed_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def get_tasks_due_for_overdue_notification(db: AsyncSession, now: datetime | None = None):
    now = now or datetime.now(timezone.utc)
    query = select(models.Task).where(
        models.Task.due_date.is_not(None),
        models.Task.due_date < now,
        models.Task.status == models.TaskStatus.PENDING,
        models.Task.notification_email.is_not(None),
        models.Task.overdue_notified_at.is_(None),
    )

    result = await db.execute(query)
    return result.scalars().all()


async def mark_task_overdue_notified(db: AsyncSession, task: models.Task):
    before_data = _task_snapshot(task)
    task.overdue_notified_at = datetime.now(timezone.utc)
    after_data = _task_snapshot(task)
    await _add_task_history(
        db=db,
        task_id=task.id,
        event_type=models.TaskEventType.NOTIFIED_OVERDUE,
        before_data=before_data,
        after_data=after_data,
        changed_fields=["overdue_notified_at"],
    )
    await db.commit()
    await db.refresh(task)
    return task


async def mark_task_completed_notified(db: AsyncSession, task: models.Task):
    before_data = _task_snapshot(task)
    task.completed_notified_at = datetime.now(timezone.utc)
    after_data = _task_snapshot(task)
    await _add_task_history(
        db=db,
        task_id=task.id,
        event_type=models.TaskEventType.NOTIFIED_COMPLETED,
        before_data=before_data,
        after_data=after_data,
        changed_fields=["completed_notified_at"],
    )
    await db.commit()
    await db.refresh(task)
    return task