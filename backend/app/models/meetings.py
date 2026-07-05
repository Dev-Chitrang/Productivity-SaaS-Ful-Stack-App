import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, JSON, Enum as SQLEnum, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from uuid6 import uuid7
from app.core.database import Base
from app.modules.meetings.enums import MeetingStatus, ParticipantType, ParticipantStatus, MeetingType, AIAnalysisStatus

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid7)
    host_id = Column(PG_UUID(as_uuid=True), index=True, nullable=False) # References system User ID

    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)

    # 10-character distinctive alpha-numeric hash (e.g. abc-defg-hij)
    meeting_code = Column(String(50), unique=True, index=True, nullable=False)
    meeting_link = Column(String(512), unique=True, nullable=False)

    enable_recording = Column(Boolean, nullable=False, default=False)
    enable_transcript = Column(Boolean, nullable=False, default=False)
    enable_ai_analysis = Column(Boolean, nullable=False, default=False)

    status = Column(SQLEnum(MeetingStatus, name="meeting_status_enum"), nullable=False, default=MeetingStatus.CREATED)

    active_screen_sharer_id = Column(PG_UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Core relationship linkage mapping to local telemetry sub-tables
    participants = relationship("MeetingParticipant", back_populates="meeting", cascade="all, delete-orphan")

    meeting_type = Column(SQLEnum(MeetingType, name="meeting_type_enum"), nullable=False, default=MeetingType.INSTANT)
    scheduled_start = Column(DateTime(timezone=True), nullable=True)
    timezone = Column(String(50), nullable=True)
    agenda = Column(String, nullable=True)
    scheduled_by = Column(PG_UUID(as_uuid=True), nullable=True)

class MeetingInvitation(Base):
    __tablename__ = "meeting_invitations"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid7)
    meeting_id = Column(PG_UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), index=True, nullable=False)

    name = Column(String(255), nullable=False)
    email = Column(String(255), index=True, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"
    __table_args__ = (
        Index("uq_meeting_participant_registered", "meeting_id", "user_id", unique=True, postgresql_where=Column("user_id").is_not(None)),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid7)
    meeting_id = Column(PG_UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), index=True, nullable=False)

    user_id = Column(PG_UUID(as_uuid=True), index=True, nullable=True) # Nullable for guest accounts
    guest_name = Column(String(100), nullable=True)                    # Populate if guest joins, display name
    guest_email = Column(String(255), nullable=True)                   # Guest identity key, unique per meeting

    participant_type = Column(SQLEnum(ParticipantType, name="participant_type_enum"), nullable=False, default=ParticipantType.REGISTERED)

    status = Column(SQLEnum(ParticipantStatus, name='participant_status_enum'), nullable=False, default=ParticipantStatus.WAITING)
    is_muted = Column(Boolean, nullable=False, default=False)
    can_start_screen_share = Column(Boolean, nullable=False, default=False)

    joined_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    left_at = Column(DateTime(timezone=True), nullable=True)

    meeting = relationship("Meeting", back_populates="participants")


class MeetingRecording(Base):
    __tablename__ = 'meeting_recordings'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid7)
    meeting_id = Column(PG_UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), index=True, nullable=False)

    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    duration = Column(Float, nullable=True)

    storage_path = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class MeetingTranscript(Base):
    __tablename__ = "meeting_transcripts"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid7)
    meeting_id = Column(PG_UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), index=True, nullable=False)

    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False, default="text/plain")
    size = Column(Integer, nullable=False, default=0)
    storage_path = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class MeetingAIAnalysis(Base):
    __tablename__ = "meeting_ai_analysis"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid7)
    meeting_id = Column(PG_UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), index=True, nullable=False)

    provider = Column(String(50), nullable=False, default="NVIDIA_NIM")
    model = Column(String(100), nullable=False, default="meta/llama-3.3-70b-instruct")

    status = Column(SQLEnum(AIAnalysisStatus, name="ai_analysis_status_enum"), nullable=False, default=AIAnalysisStatus.PENDING)

    summary = Column(String, nullable=True)
    agenda_coverage_percentage = Column(Integer, nullable=True)

    # JSON structural breakdowns
    covered_points = Column(JSON, nullable=True)          # List[str]
    out_of_agenda_points = Column(JSON, nullable=True)     # List[str]
    suggested_tasks = Column(JSON, nullable=True)          # List[dict(title, description, priority)]
    raw_response = Column(JSON, nullable=True)

    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
