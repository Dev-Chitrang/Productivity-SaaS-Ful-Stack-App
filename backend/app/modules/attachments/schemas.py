from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.modules.attachments.enums import AttachmentEntityType


# ── Request schemas ───────────────────────────────────────────────────────────

class AttachmentUploadContext(BaseModel):
    """
    Carries the resolved metadata after the upload file has been validated.
    This is an internal transfer object, not a user-facing request body
    (the file itself arrives as UploadFile via multipart form).
    """
    entity_type: AttachmentEntityType
    entity_id: UUID


# ── Response schemas ──────────────────────────────────────────────────────────

class AttachmentResponse(BaseModel):
    """Public-facing representation of an attachment record."""
    id: UUID
    owner_user_id: UUID
    entity_type: AttachmentEntityType
    entity_id: UUID
    original_filename: str
    stored_filename: str
    content_type: str
    extension: str
    size: int
    storage_provider: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AttachmentListResponse(BaseModel):
    attachments: list[AttachmentResponse]
    total_count: int
