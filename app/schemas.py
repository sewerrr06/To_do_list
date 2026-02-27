from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any, List
from .models import TaskStatus, TaskEventType
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


class TaskHistoryResponse(BaseModel):
    id: int
    task_id: int
    event_type: TaskEventType
    changed_at: datetime
    before_data: Optional[dict[str, Any]] = None
    after_data: Optional[dict[str, Any]] = None
    changed_fields: Optional[List[str]] = None

    class Config:
        from_attributes = True