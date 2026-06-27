from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator
from app.modules.notes.constants import MAX_NOTE_TITLE_LENGTH, MAX_NOTE_CONTENT_LENGTH

class NoteBase(BaseModel):
    title: Optional[str] = Field(None, max_length=MAX_NOTE_TITLE_LENGTH, description="Optional note title.")
    content: str = Field(..., max_length=MAX_NOTE_CONTENT_LENGTH, description="The main text body content of the note.")
    category: Optional[str] = Field(None, max_length=100, description="Optional classification category.")
    tags: List[str] = Field(default_factory=list, description="Array of tags attached to the note.")
    is_pinned: bool = Field(default=False)
    is_favorite: bool = Field(default=False)
    is_archived: bool = Field(default=False)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            return value.strip()
        return value

    @field_validator("tags")
    @classmethod
    def clean_and_deduplicate_tags(cls, value: List[str]) -> List[str]:
        # Strip whitespace, convert to lower for consistent search indexing, and deduplicate
        return list(set(tag.strip().lower() for tag in value if tag and tag.strip()))

class NoteCreate(NoteBase):
    @model_validator(mode="after")
    def validate_non_empty_note(self) -> "NoteCreate":
        # Ensure that empty titles are only allowed if actual text content is supplied
        has_title = self.title and self.title.strip()
        has_content = self.content and self.content.strip()

        if not has_title and not has_content:
            raise ValueError("Empty notes are prohibited. You must supply a valid title or content string.")
        return self

class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=MAX_NOTE_TITLE_LENGTH)
    content: Optional[str] = Field(None, max_length=MAX_NOTE_CONTENT_LENGTH)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_patch_bounds(self) -> "NoteUpdate":
        # Guard against zero-length content configurations during inline updates
        if self.content is not None and not self.content.strip() and (self.title is None or not self.title.strip()):
            raise ValueError("Cannot strip notes down to an entirely empty state.")
        return self

class NoteResponse(NoteBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NoteListResponse(BaseModel):
    notes: List[NoteResponse]
    total_count: int
