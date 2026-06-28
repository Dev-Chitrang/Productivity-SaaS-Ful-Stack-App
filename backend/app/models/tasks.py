import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from uuid6 import uuid7
from app.core.database import Base
from app.modules.tasks.enums import TaskStatus, TaskPriority

class Task(Base):
    __tablename__ = "tasks"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid7)
    user_id = Column(PG_UUID(as_uuid=True), index=True, nullable=False)

    title = Column(String(255), nullable=False)
    # Storing rich description JSON structure matching Notes layout
    description = Column(JSONB, nullable=True)

    status = Column(SQLEnum(TaskStatus, name="task_status_enum"), nullable=False, default=TaskStatus.TODO)
    priority = Column(SQLEnum(TaskPriority, name="task_priority_enum"), nullable=False, default=TaskPriority.MEDIUM)
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)

    # Embedded JSON structures
    labels = Column(JSONB, nullable=False, default=list) # Flat JSON string array
    checklist = Column(JSONB, nullable=False, default=list) # Array of objects: {"id": str, "text": str, "completed": bool}

    # UI/State Flags
    is_pinned = Column(Boolean, nullable=False, default=False)
    is_favorite = Column(Boolean, nullable=False, default=False)
    is_archived = Column(Boolean, nullable=False, default=False)

    # Audit trail
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime(timezone=True), nullable=True)

class TaskHistory(Base):
    __tablename__ = "task_history"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid7)
    task_id = Column(PG_UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), index=True, nullable=False)

    action = Column(String(50), nullable=False) # e.g., "CREATED", "UPDATED", "DELETED", "ARCHIVED"
    field_name = Column(String(50), nullable=True) # e.g., "status", "due_date" (Null for creations/deletions)
    old_value = Column(String, nullable=True) # Stringified variant or JSON snippet
    new_value = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
