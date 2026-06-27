import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from uuid6 import uuid7
from app.core.database import Base

class Note(Base):
    __tablename__ = "notes"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid7)
    user_id = Column(PG_UUID(as_uuid=True), index=True, nullable=False) # Maps to auth User ID

    title = Column(String(255), nullable=True)
    content = Column(String, nullable=False)
    category = Column(String(100), nullable=True, index=True)

    # Storing flat string arrays securely inside high-performance binary JSON fields
    tags = Column(JSONB, nullable=False, default=list)

    # State flags
    is_pinned = Column(Boolean, nullable=False, default=False)
    is_favorite = Column(Boolean, nullable=False, default=False)
    is_archived = Column(Boolean, nullable=False, default=False)

    # Auditing Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime(timezone=True), nullable=True) # Operational target for explicit soft-delete routines
