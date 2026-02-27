from fastapi import FastAPI, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from . import models, schemas, crud
from .database import get_db

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="To-Do List API", description="REST API для управління завданнями")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/tasks/", response_model=schemas.TaskResponse, status_code=201)
@limiter.limit("5/minute")  
async def create_task(request: Request, task: schemas.TaskCreate, db: AsyncSession = Depends(get_db)):
    """Створення нового завдання."""
    return await crud.create_task(db=db, task=task)

@app.get("/tasks/", response_model=List[schemas.TaskResponse])
async def read_tasks(
    skip: int = Query(0, description="Пропустити N записів"),
    limit: int = Query(10, description="Кількість записів на сторінку"),
    status: Optional[models.TaskStatus] = Query(None, description="Фільтр за статусом: pending або completed"),
    db: AsyncSession = Depends(get_db)
):
    """Отримання списку завдань із пагінацією та фільтром статусу."""
    return await crud.get_tasks(db=db, skip=skip, limit=limit, status=status)

@app.get("/tasks/{task_id}", response_model=schemas.TaskResponse)
async def read_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Отримання конкретного завдання за ID."""
    task = await crud.get_task(db=db, task_id=task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Завдання не знайдено")
    return task

@app.patch("/tasks/{task_id}", response_model=schemas.TaskResponse)
async def update_task(task_id: int, task: schemas.TaskUpdate, db: AsyncSession = Depends(get_db)):
    """Оновлення завдання."""
    existing_task = await crud.get_task(db=db, task_id=task_id)
    if existing_task is None:
        raise HTTPException(status_code=404, detail="Завдання не знайдено")

    status_before = existing_task.status
    updated_task = await crud.update_task(db=db, task_id=task_id, task_update=task)
    if updated_task is None:
        raise HTTPException(status_code=404, detail="Завдання не знайдено")

    if status_before != models.TaskStatus.COMPLETED and updated_task.status == models.TaskStatus.COMPLETED:
        from .celery_app import send_task_completed_email

        send_task_completed_email.delay(updated_task.id)

    return updated_task

@app.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Видалення завдання."""
    success = await crud.delete_task(db=db, task_id=task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Завдання не знайдено")