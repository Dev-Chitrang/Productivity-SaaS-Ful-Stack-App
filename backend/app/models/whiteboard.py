import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from uuid6 import uuid7
from app.core.database import Base

class Whiteboard(Base):
    __tablename__ = "whiteboards"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid7)
    user_id = Column(PG_UUID(as_uuid=True), index=True, nullable=False)

    title = Column(String(255), nullable=False)
    # Using JSONB over standard JSON for optimized indexation and update execution
    board_data = Column(JSONB, nullable=False, default=lambda: {"version": 1, "elements": []})

    is_favorite = Column(Boolean, nullable=False, default=False)
    is_archived = Column(Boolean, nullable=False, default=False)
    is_deleted = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime(timezone=True), nullable=True)
