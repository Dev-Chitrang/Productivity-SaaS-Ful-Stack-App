from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from app.modules.meetings.enums import MeetingStatus, ParticipantType, ParticipantStatus
from app.modules.meetings.constants import MAX_MEETING_TITLE_LENGTH, MAX_GUEST_NAME_LENGTH, MAX_GUEST_EMAIL_LENGTH

class MeetingBase(BaseModel):
    title: str = Field(..., max_length=MAX_MEETING_TITLE_LENGTH)
    description: Optional[str] = None
    enable_recording: bool = False
    enable_transcript: bool = False

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
    active_screen_sharer_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    ended_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MeetingParticipantResponse(BaseModel):
    id: UUID
    meeting_id: UUID
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
    meeting_id: UUID
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
    meeting_id: UUID
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
    meeting_id: UUID
    filename: str
    content_type: str
    size: int
    created_at: datetime

    class Config:
        from_attributes = True
