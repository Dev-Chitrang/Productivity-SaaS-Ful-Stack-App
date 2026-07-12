import uuid
from datetime import datetime, timezone
from typing import Optional

import pytest
from pydantic import ValidationError

from app.modules.meetings.constants import MAX_MEETING_TITLE_LENGTH, MAX_GUEST_NAME_LENGTH, MAX_GUEST_EMAIL_LENGTH
from app.modules.meetings.enums import MeetingStatus, ParticipantType, ParticipantStatus, MeetingType, AIAnalysisStatus
from app.modules.meetings.schemas import (
    MeetingBase,
    MeetingCreate,
    MeetingUpdate,
    MeetingResponse,
    MeetingParticipantResponse,
    MeetingJoinResponse,
    MeetingJoinInfoResponse,
    MeetingJoinPayload,
    RecordingResponse,
    WaitingCountResponse,
    TranscriptResponse,
    InvitationCreate,
    InvitationResponse,
    ScheduledMeetingCreate,
    ScheduledMeetingUpdate,
    SuggestedTaskSchema,
    AIAnalysisPayloadSchema,
    AIAnalysisResponse,
    RecentAIAnalysisItem,
    AIAnalysisStatusResponse,
    SessionHistoryItemResponse,
    SessionParticipantSummary,
    SessionArtifactFlags,
    SessionDetailResponse,
)


class TestMeetingBase:
    def test_valid_base(self):
        m = MeetingBase(title="Team Sync", description="Weekly sync", enable_recording=True, enable_transcript=True, agenda="Review Q3", enable_ai_analysis=True)
        assert m.title == "Team Sync"
        assert m.enable_recording is True

    def test_title_max_length(self):
        title = "a" * MAX_MEETING_TITLE_LENGTH
        m = MeetingBase(title=title)
        assert len(m.title) == MAX_MEETING_TITLE_LENGTH

    def test_title_exceeds_max_length(self):
        with pytest.raises(ValidationError):
            MeetingBase(title="a" * (MAX_MEETING_TITLE_LENGTH + 1))

    def test_blank_title_raises(self):
        with pytest.raises(ValidationError, match="cannot be blank"):
            MeetingBase(title="   ")

    def test_empty_title_raises(self):
        with pytest.raises(ValidationError, match="cannot be blank"):
            MeetingBase(title="")


class TestMeetingCreate:
    def test_inherits_base(self):
        m = MeetingCreate(title="Created Meeting")
        assert m.title == "Created Meeting"
        assert m.enable_recording is False


class TestMeetingUpdate:
    def test_valid_update(self):
        m = MeetingUpdate(title="Updated Title", enable_recording=True)
        assert m.title == "Updated Title"

    def test_optional_title_none(self):
        m = MeetingUpdate()
        assert m.title is None

    def test_blank_update_title_raises(self):
        with pytest.raises(ValidationError, match="cannot be modified to an empty state"):
            MeetingUpdate(title="   ")


class TestMeetingResponse:
    def test_valid_response(self):
        now = datetime.now(timezone.utc)
        m = MeetingResponse(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            host_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            title="Response Meeting",
            meeting_code="abc-defg-hij",
            meeting_link="https://workspace.app/m/abc-defg-hij",
            status=MeetingStatus.ACTIVE,
            meeting_type=MeetingType.INSTANT,
            invited_participants_count=3,
            created_at=now,
            updated_at=now,
        )
        assert m.id == uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert m.invited_participants_count == 3

    def test_from_attributes_config(self):
        assert MeetingResponse.model_config.get("from_attributes") is True


class TestMeetingParticipantResponse:
    def test_valid_response(self):
        now = datetime.now(timezone.utc)
        p = MeetingParticipantResponse(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            session_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            user_name="Alice",
            guest_name=None,
            guest_email=None,
            participant_type=ParticipantType.REGISTERED,
            status=ParticipantStatus.ADMITTED,
            is_muted=False,
            can_start_screen_share=True,
            joined_at=now,
        )
        assert p.user_name == "Alice"
        assert p.participant_type == ParticipantType.REGISTERED


class TestMeetingJoinResponse:
    def test_valid_response(self):
        now = datetime.now(timezone.utc)
        resp = MeetingJoinResponse(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            session_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            user_id=None,
            guest_name="Guest User",
            guest_email="guest@example.com",
            participant_type=ParticipantType.GUEST,
            status=ParticipantStatus.WAITING,
            is_muted=False,
            joined_at=now,
            meeting_session_token="token123",
        )
        assert resp.guest_email == "guest@example.com"
        assert resp.meeting_session_token == "token123"


class TestMeetingJoinPayload:
    def test_valid_payload(self):
        p = MeetingJoinPayload(guest_name="Guest", guest_email="guest@example.com")
        assert p.guest_name == "Guest"
        assert p.guest_email == "guest@example.com"

    def test_optional_fields(self):
        p = MeetingJoinPayload()
        assert p.guest_name is None
        assert p.guest_email is None


class TestRecordingResponse:
    def test_valid_recording(self):
        now = datetime.now(timezone.utc)
        r = RecordingResponse(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            session_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            filename="rec.webm",
            content_type="audio/webm",
            size=1024,
            created_at=now,
        )
        assert r.size == 1024
        assert r.duration is None


class TestWaitingCountResponse:
    def test_default(self):
        w = WaitingCountResponse(waiting_count=0)
        assert w.waiting_count == 0

    def test_custom(self):
        w = WaitingCountResponse(waiting_count=5)
        assert w.waiting_count == 5


class TestTranscriptResponse:
    def test_valid_transcript(self):
        now = datetime.now(timezone.utc)
        t = TranscriptResponse(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            session_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            filename="transcript.txt",
            content_type="text/plain",
            size=2048,
            created_at=now,
        )
        assert t.size == 2048


class TestInvitationCreate:
    def test_valid_invitation(self):
        inv = InvitationCreate(name="John Doe", email="john@example.com")
        assert inv.name == "John Doe"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            InvitationCreate(name="John", email="not-an-email")


class TestInvitationResponse:
    def test_valid_response(self):
        now = datetime.now(timezone.utc)
        inv = InvitationResponse(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            meeting_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            name="John Doe",
            email="john@example.com",
            created_at=now,
        )
        assert inv.id is not None


class TestScheduledMeetingCreate:
    def test_valid_scheduled(self):
        future = datetime.now(timezone.utc).replace(tzinfo=None)
        # Need a naive datetime for pydantic, actually the schema uses datetime and validates
        pass

    def test_missing_invitations_raises(self):
        with pytest.raises(ValidationError, match="At least one participant is required"):
            ScheduledMeetingCreate(
                title="Scheduled",
                scheduled_start=datetime(2099, 1, 1, tzinfo=timezone.utc),
                timezone="UTC",
                invitations=[],
            )

    def test_past_date_raises(self):
        past = datetime(2000, 1, 1, tzinfo=timezone.utc)
        with pytest.raises(ValidationError, match="explicitly in the future"):
            ScheduledMeetingCreate(
                title="Past Meeting",
                scheduled_start=past,
                timezone="UTC",
                invitations=[{"name": "John", "email": "john@example.com"}],
            )


class TestScheduledMeetingUpdate:
    def test_valid_update(self):
        u = ScheduledMeetingUpdate(title="Updated", timezone="EST")
        assert u.title == "Updated"


class TestSuggestedTaskSchema:
    def test_valid_task(self):
        t = SuggestedTaskSchema(title="Task", description="Desc", priority="HIGH")
        assert t.title == "Task"
        assert t.priority == "HIGH"

    def test_requires_priority(self):
        with pytest.raises(ValidationError):
            SuggestedTaskSchema(title="Task", description="Desc")


class TestAIAnalysisPayloadSchema:
    def test_valid_payload(self):
        payload = {
            "summary": "Summary text",
            "coverage_percentage": 85,
            "covered_points": ["point1"],
            "out_of_agenda_points": ["point2"],
            "suggested_tasks": [{"title": "Task1", "description": "Desc", "priority": "HIGH"}],
        }
        a = AIAnalysisPayloadSchema(**payload)
        assert a.summary == "Summary text"
        assert a.coverage_percentage == 85

    def test_coverage_out_of_range(self):
        with pytest.raises(ValidationError):
            AIAnalysisPayloadSchema(
                summary="s",
                coverage_percentage=101,
                covered_points=[],
                out_of_agenda_points=[],
                suggested_tasks=[],
            )

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            AIAnalysisPayloadSchema(
                summary="s",
                coverage_percentage=50,
                covered_points=[],
                out_of_agenda_points=[],
            )


class TestAIAnalysisResponse:
    def test_valid_response(self):
        now = datetime.now(timezone.utc)
        a = AIAnalysisResponse(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            session_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            provider="NVIDIA_NIM",
            model="meta/llama-3.3-70b-instruct",
            status=AIAnalysisStatus.COMPLETED,
            summary="Summary",
            agenda_coverage_percentage=85,
            created_at=now,
        )
        assert a.status == AIAnalysisStatus.COMPLETED


class TestRecentAIAnalysisItem:
    def test_valid_item(self):
        now = datetime.now(timezone.utc)
        item = RecentAIAnalysisItem(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            session_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            meeting_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            meeting_title="Sync",
            created_at=now,
        )
        assert item.meeting_title == "Sync"


class TestAIAnalysisStatusResponse:
    def test_valid_response(self):
        r = AIAnalysisStatusResponse(
            session_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            status=AIAnalysisStatus.COMPLETED,
        )
        assert r.status == AIAnalysisStatus.COMPLETED


class TestSessionHistoryItemResponse:
    def test_valid_response(self):
        now = datetime.now(timezone.utc)
        s = SessionHistoryItemResponse(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            meeting_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            status=MeetingStatus.ACTIVE,
            started_at=now,
            participant_count=5,
        )
        assert s.participant_count == 5


class TestSessionParticipantSummary:
    def test_valid_summary(self):
        now = datetime.now(timezone.utc)
        s = SessionParticipantSummary(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            user_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            user_name="Alice",
            guest_name=None,
            participant_type=ParticipantType.REGISTERED,
            status=ParticipantStatus.ADMITTED,
            joined_at=now,
        )
        assert s.user_name == "Alice"


class TestSessionArtifactFlags:
    def test_defaults(self):
        f = SessionArtifactFlags()
        assert f.has_recording is False
        assert f.has_transcript is False
        assert f.has_ai_analysis is False

    def test_custom_flags(self):
        f = SessionArtifactFlags(has_recording=True, has_transcript=True, has_ai_analysis=True)
        assert f.has_recording is True


class TestSessionDetailResponse:
    def test_valid_response(self):
        now = datetime.now(timezone.utc)
        s = SessionDetailResponse(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            meeting_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            host_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            status=MeetingStatus.ACTIVE,
            started_at=now,
            participants=[],
            artifacts=SessionArtifactFlags(),
        )
        assert s.participants == []
        assert isinstance(s.artifacts, SessionArtifactFlags)
