import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid6 import uuid7
from app.core.database import Base
from app.modules.calender.enums import EventType, EventColor, RecurrenceFrequency

class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid7)
    user_id = Column(PG_UUID(as_uuid=True), index=True, nullable=False) # Maps to auth User ID

    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)

    event_type = Column(SQLEnum(EventType, name="event_type_enum"), nullable=False, default=EventType.PERSONAL)
    color = Column(SQLEnum(EventColor, name="event_color_enum"), nullable=False, default=EventColor.BLUE)

    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    timezone = Column(String(100), nullable=False, default="UTC")
    is_all_day = Column(Boolean, nullable=False, default=False)
    location = Column(String(500), nullable=True)

    # Recurrence Metadata Strategy
    recurrence_frequency = Column(SQLEnum(RecurrenceFrequency, name="recurrence_frequency_enum"), nullable=True)
    recurrence_interval = Column(Integer, nullable=True)
    recurrence_end_date = Column(DateTime(timezone=True), nullable=True)

    # Audit Hooks
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime(timezone=True), nullable=True) # Soft-delete timeline target
