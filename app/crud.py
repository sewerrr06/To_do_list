from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import models, schemas
from datetime import datetime, timezone

async def create_task(db: AsyncSession, task: schemas.TaskCreate):
    db_task = models.Task(**task.model_dump())
    db.add(db_task)
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

    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)

    await db.commit()
    await db.refresh(db_task)
    return db_task

async def delete_task(db: AsyncSession, task_id: int):
    db_task = await get_task(db, task_id)
    if db_task:
        await db.delete(db_task)
        await db.commit()
        return True
    return False

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
    task.overdue_notified_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(task)
    return task


async def mark_task_completed_notified(db: AsyncSession, task: models.Task):
    task.completed_notified_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(task)
    return task