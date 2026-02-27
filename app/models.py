from sqlalchemy import Column, Integer, String, DateTime, Enum, JSON
from datetime import datetime, timezone
import enum
from .database import Base

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"


class TaskEventType(str, enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    STATUS_CHANGED = "status_changed"
    DELETED = "deleted"
    NOTIFIED_COMPLETED = "notified_completed"
    NOTIFIED_OVERDUE = "notified_overdue"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    notification_email = Column(String, nullable=True)
    completed_notified_at = Column(DateTime, nullable=True)
    overdue_notified_at = Column(DateTime, nullable=True)


class TaskHistory(Base):
    __tablename__ = "task_history"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, index=True, nullable=False)
    event_type = Column(Enum(TaskEventType), nullable=False, index=True)
    changed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    before_data = Column(JSON, nullable=True)
    after_data = Column(JSON, nullable=True)
    changed_fields = Column(JSON, nullable=True)