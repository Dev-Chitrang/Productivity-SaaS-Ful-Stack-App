import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, Time, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid6 import uuid7
from app.core.database import Base

class UserReminderSetting(Base):
    __tablename__ = "user_reminder_settings"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid7)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    reminders_enabled = Column(Boolean, nullable=False, default=False)

    schedule_all = Column(Boolean, nullable=False, default=True)

    # Global Config State Fallbacks
    global_frequency = Column(String(20), nullable=True, default="DAILY")
    global_time = Column(Time, nullable=True, default=None)

    # Granular Module Configurations stored as structured maps:
    # {"enabled": bool, "frequency": str, "time": str}
    calendar_config = Column(JSON, nullable=False, default=lambda: {"enabled": False, "frequency": "DAILY", "time": "09:00:00"})
    tasks_config = Column(JSON, nullable=False, default=lambda: {"enabled": False, "frequency": "DAILY", "time": "09:00:00"})
    meetings_config = Column(JSON, nullable=False, default=lambda: {"enabled": False, "frequency": "DAILY", "time": "09:00:00"})
