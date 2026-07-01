from datetime import datetime
from typing import Optional, Any, Dict, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

class WhiteboardBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Whiteboard title cannot be empty or solely whitespace.")
        return value.strip()

class WhiteboardCreate(WhiteboardBase):
    # Initialize with default structure if empty canvas payload is provided
    board_data: Dict[str, Any] = Field(default_factory=lambda: {"version": 1, "elements": []})

class WhiteboardRename(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)

    @field_validator("title")
    @classmethod
    def validate_rename_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("New whiteboard title cannot be blank.")
        return value.strip()

class WhiteboardAutosave(BaseModel):
    board_data: Dict[str, Any]

class WhiteboardResponse(WhiteboardBase):
    id: UUID
    user_id: UUID
    board_data: Dict[str, Any]
    is_favorite: bool
    is_archived: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class WhiteboardFilters(BaseModel):
    is_archived: Optional[bool] = False
    is_deleted: Optional[bool] = False
    is_favorite: Optional[bool] = None
    search: Optional[str] = None
