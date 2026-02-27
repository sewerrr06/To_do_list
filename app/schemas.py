from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from .models import TaskStatus
from pydantic import EmailStr

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="Назва завдання")
    description: Optional[str] = Field(None, description="Опис завдання")
    due_date: Optional[datetime] = Field(None, description="Дедлайн виконання")
    notification_email: Optional[EmailStr] = Field(None, description="Email для сповіщень")

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None
    notification_email: Optional[EmailStr] = None

class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    created_at: datetime

    class Config:
        from_attributes = True