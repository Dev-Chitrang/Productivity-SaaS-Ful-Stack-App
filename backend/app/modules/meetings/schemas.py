from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, EmailStr, model_validator
from app.modules.meetings.enums import MeetingStatus, ParticipantType, ParticipantStatus, MeetingType, AIAnalysisStatus, SessionStatus
from app.modules.meetings.constants import MAX_MEETING_TITLE_LENGTH, MAX_GUEST_NAME_LENGTH, MAX_GUEST_EMAIL_LENGTH

class MeetingBase(BaseModel):
    title: str = Field(..., max_length=MAX_MEETING_TITLE_LENGTH)
    description: Optional[str] = None
    enable_recording: bool = False
    enable_transcript: bool = False
    agenda: Optional[str] = None
    enable_ai_analysis: bool = False

    @field_validator("title")
    @classmethod
    def validate_title_not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Meeting title cannot be blank or white space.")
        return value.strip()

class MeetingCreate(MeetingBase):
    pass

class MeetingUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=MAX_MEETING_TITLE_LENGTH)
    description: Optional[str] = None
    enable_recording: Optional[bool] = None
    enable_transcript: Optional[bool] = None
    agenda: Optional[str] = None
    enable_ai_analysis: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def validate_optional_title(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("Meeting title cannot be modified to an empty state.")
        return value

class MeetingResponse(MeetingBase):
    id: UUID
    host_id: UUID
    meeting_code: str
    meeting_link: str
    status: MeetingStatus
    meeting_type: MeetingType = MeetingType.INSTANT
    scheduled_start: Optional[datetime] = None
    timezone: Optional[str] = None
    active_screen_sharer_id: Optional[UUID] = None
    invited_participants_count: int = 0
    created_at: datetime
    updated_at: datetime
    ended_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MeetingParticipantResponse(BaseModel):
    id: UUID
    session_id: UUID
    user_id: Optional[UUID] = None
    user_name: Optional[str] = None
    guest_name: Optional[str] = None
    guest_email: Optional[str] = None
    participant_type: ParticipantType
    status: ParticipantStatus
    is_muted: bool
    can_start_screen_share: bool = False
    joined_at: datetime
    left_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MeetingJoinResponse(BaseModel):
    id: UUID
    session_id: UUID
    user_id: Optional[UUID] = None
    guest_name: Optional[str] = None
    guest_email: Optional[str] = None
    participant_type: ParticipantType
    status: ParticipantStatus
    is_muted: bool
    can_start_screen_share: bool = False
    joined_at: datetime
    left_at: Optional[datetime] = None
    meeting_session_token: str

    class Config:
        from_attributes = True

class MeetingJoinInfoResponse(MeetingResponse):
    host_name: str

class MeetingJoinPayload(BaseModel):
    guest_name: Optional[str] = Field(None, max_length=MAX_GUEST_NAME_LENGTH)
    guest_email: Optional[str] = Field(None, max_length=MAX_GUEST_EMAIL_LENGTH)

class RecordingResponse(BaseModel):
    id: UUID
    session_id: UUID
    filename: str
    content_type: str
    size: int
    duration: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

class WaitingCountResponse(BaseModel):
    waiting_count: int

class TranscriptResponse(BaseModel):
    id: UUID
    session_id: UUID
    filename: str
    content_type: str
    size: int
    created_at: datetime

    class Config:
        from_attributes = True

class InvitationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr

class InvitationResponse(InvitationCreate):
    id: UUID
    meeting_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class ScheduledMeetingCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    enable_recording: bool = False
    enable_transcript: bool = False
    enable_ai_analysis: bool = False
    agenda: Optional[str] = None
    scheduled_start: datetime
    # Optional — if omitted the host's profile timezone is used; falls back to UTC.
    timezone: Optional[str] = Field(None, max_length=64)
    invitations: List[InvitationCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_future_date(self):
        if self.scheduled_start <= datetime.now(timezone.utc):
            raise ValueError("Scheduled start time must be explicitly in the future.")
        return self

    @model_validator(mode="after")
    def validate_invitations(self):
        if not self.invitations:
            raise ValueError("At least one participant is required.")
        for i, invite in enumerate(self.invitations):
            if not invite.name or not invite.name.strip():
                raise ValueError(f"Participant {i + 1}: name is required.")
            if not invite.email:
                raise ValueError(f"Participant {i + 1}: email is required.")
        return self

class ScheduledMeetingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    enable_recording: Optional[bool] = None
    enable_transcript: Optional[bool] = None
    enable_ai_analysis: Optional[bool] = None
    agenda: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    timezone: Optional[str] = None

class SuggestedTaskSchema(BaseModel):
    title: str
    description: str
    priority: str

class AIAnalysisPayloadSchema(BaseModel):
    """Matches the exact structural format required from the LLM engine generation output."""
    summary: str
    coverage_percentage: int = Field(..., ge=0, le=100)
    covered_points: List[str]
    out_of_agenda_points: List[str]
    suggested_tasks: List[SuggestedTaskSchema]

class AIAnalysisResponse(BaseModel):
    id: UUID
    session_id: UUID
    provider: str
    model: str
    status: AIAnalysisStatus
    summary: Optional[str] = None
    agenda_coverage_percentage: Optional[int] = None
    covered_points: Optional[List[str]] = None
    out_of_agenda_points: Optional[List[str]] = None
    suggested_tasks: Optional[List[SuggestedTaskSchema]] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class RecentAIAnalysisItem(BaseModel):
    id: UUID
    session_id: UUID
    meeting_id: Optional[UUID] = None
    meeting_title: Optional[str] = None
    session_date: Optional[datetime] = None
    status: Optional[AIAnalysisStatus] = None
    summary: Optional[str] = None
    agenda_coverage_percentage: Optional[int] = None
    processing_completed_at: Optional[datetime] = None
    created_at: datetime


class AIAnalysisStatusResponse(BaseModel):
    session_id: UUID
    status: AIAnalysisStatus
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Session History schemas (Phase 5)
# ---------------------------------------------------------------------------


class SessionHistoryItemResponse(BaseModel):
    """Lightweight row returned in the session list (host or participant view)."""
    id: UUID
    meeting_id: UUID
    status: SessionStatus
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    participant_count: int = 0

    class Config:
        from_attributes = True


class SessionParticipantSummary(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    user_name: Optional[str] = None
    guest_name: Optional[str] = None
    participant_type: ParticipantType
    status: ParticipantStatus
    joined_at: datetime
    left_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionArtifactFlags(BaseModel):
    has_recording: bool = False
    has_transcript: bool = False
    has_ai_analysis: bool = False


class SessionDetailResponse(BaseModel):
    """Full session detail including participants and artifact availability flags."""
    id: UUID
    meeting_id: UUID
    host_id: UUID
    status: SessionStatus
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    participants: List[SessionParticipantSummary] = []
    artifacts: SessionArtifactFlags = SessionArtifactFlags()

    class Config:
        from_attributes = True
