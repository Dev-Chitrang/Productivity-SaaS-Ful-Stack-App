from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
from app.modules.ai_suggestions.enums import SuggestionStatus


class SuggestionResponse(BaseModel):
    id: UUID
    analysis_id: UUID
    title: str
    description: Optional[str] = None
    priority: str
    status: SuggestionStatus
    created_task_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SuggestionListResponse(BaseModel):
    suggestions: List[SuggestionResponse]
    total_count: int


class CreateTaskFromSuggestionPayload(BaseModel):
    title: Optional[str] = Field(None, description="Optional override for the task title")
