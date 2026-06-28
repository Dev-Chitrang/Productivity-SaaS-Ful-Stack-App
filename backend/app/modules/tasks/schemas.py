from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator
from app.modules.tasks.enums import TaskStatus, TaskPriority
from app.modules.tasks.constants import MAX_TASK_TITLE_LENGTH

class ChecklistItem(BaseModel):
    id: str = Field(..., description="Unique client-generated string identifier for the sub-item.")
    text: str = Field(..., description="The actionable string descriptive content of the item.")
    completed: bool = Field(default=False)

    @field_validator("text")
    @classmethod
    def clean_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Checklist item text cannot be empty.")
        return value.strip()

class TaskBase(BaseModel):
    title: str = Field(..., max_length=MAX_TASK_TITLE_LENGTH)
    description: Optional[Dict[str, Any]] = Field(None, description="Rich description structured payload.")
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    labels: List[str] = Field(default_factory=list)
    checklist: List[ChecklistItem] = Field(default_factory=list)
    is_pinned: bool = False
    is_favorite: bool = False
    is_archived: bool = False

    @field_validator("title")
    @classmethod
    def validate_title_content(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Task title is required and cannot be blank.")
        return value.strip()

    @field_validator("labels")
    @classmethod
    def process_and_deduplicate_labels(cls, value: List[str]) -> List[str]:
        return list(set(label.strip().lower() for label in value if label and label.strip()))

class TaskCreate(TaskBase):
    @model_validator(mode="after")
    def validate_future_due_date(self) -> "TaskCreate":
        if self.due_date:
            due_date = self.due_date
            if due_date.tzinfo is None:
                due_date = due_date.replace(tzinfo=timezone.utc)
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            if due_date < today_start:
                raise ValueError("Task due_date cannot be set in the past.")
        return self

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=MAX_TASK_TITLE_LENGTH)
    description: Optional[Dict[str, Any]] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    labels: Optional[List[str]] = None
    checklist: Optional[List[ChecklistItem]] = None

    @field_validator("title")
    @classmethod
    def validate_optional_title(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("Task title cannot be updated to an empty string.")
        return value

class TaskResponse(TaskBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total_count: int


class UserInfo(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True

class TaskHistoryResponse(BaseModel):
    id: UUID
    action: str
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    created_at: datetime
    user: UserInfo

    class Config:
        from_attributes = True

class TaskHistoryListResponse(BaseModel):
    history: List[TaskHistoryResponse]
    total_count: int
