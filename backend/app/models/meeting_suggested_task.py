from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid6 import uuid7
from app.core.database import Base
from app.modules.ai_suggestions.enums import SuggestionStatus


class MeetingSuggestedTask(Base):
    __tablename__ = "meeting_suggested_tasks"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid7)
    analysis_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("meeting_ai_analysis.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    priority = Column(String(20), nullable=False, default="MEDIUM")

    status = Column(
        SQLEnum(SuggestionStatus, name="suggestion_status_enum"),
        nullable=False,
        default=SuggestionStatus.PENDING,
    )

    created_task_id = Column(PG_UUID(as_uuid=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
