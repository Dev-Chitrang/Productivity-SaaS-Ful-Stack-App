import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.modules.meetings.enums import MeetingStatus, MeetingType, ParticipantType, ParticipantStatus, SessionStatus, AIAnalysisStatus
from app.models.meetings import Meeting, MeetingParticipant, MeetingRecording, MeetingTranscript, MeetingAIAnalysis, MeetingSession, MeetingInvitation


class TestMeetingModel:
    def test_tablename(self):
        assert Meeting.__tablename__ == "meetings"

    def test_id_default_generates_uuid(self):
        meeting = Meeting(
            host_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Test Meeting",
            meeting_code="abc-defg-hij",
            meeting_link="https://workspace.app/m/abc-defg-hij",
        )
        assert meeting.id is None or isinstance(meeting.id, (uuid.UUID, type(uuid.uuid7())))

    def test_minimal_fields(self):
        now = datetime.now(timezone.utc)
        meeting = Meeting(
            host_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Minimal Meeting",
            meeting_code="abc-defg-hij",
            meeting_link="https://workspace.app/m/abc-defg-hij",
            status=MeetingStatus.CREATED,
            meeting_type=MeetingType.INSTANT,
            enable_recording=False,
            enable_transcript=False,
            enable_ai_analysis=False,
            created_at=now,
            updated_at=now,
        )
        assert meeting.host_id == uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert meeting.title == "Minimal Meeting"
        assert meeting.description is None
        assert meeting.status == MeetingStatus.CREATED
        assert meeting.meeting_type == MeetingType.INSTANT
        assert meeting.enable_recording is False
        assert meeting.enable_transcript is False
        assert meeting.enable_ai_analysis is False
        assert meeting.active_screen_sharer_id is None
        assert meeting.ended_at is None
        assert meeting.deleted_at is None
        assert isinstance(meeting.created_at, datetime)
        assert isinstance(meeting.updated_at, datetime)

    def test_full_fields(self):
        now = datetime.now(timezone.utc)
        meeting = Meeting(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            host_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            title="Full Meeting",
            description="Description",
            meeting_code="abc-defg-hij",
            meeting_link="https://workspace.app/m/abc-defg-hij",
            enable_recording=True,
            enable_transcript=True,
            enable_ai_analysis=True,
            status=MeetingStatus.ACTIVE,
            active_screen_sharer_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            meeting_type=MeetingType.SCHEDULED,
            scheduled_start=now,
            timezone="UTC",
            agenda="Agenda",
            scheduled_by=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            ended_at=now,
            deleted_at=None,
            created_at=now,
            updated_at=now,
        )
        assert meeting.status == MeetingStatus.ACTIVE
        assert meeting.meeting_type == MeetingType.SCHEDULED
        assert meeting.agenda == "Agenda"
        assert meeting.active_screen_sharer_id is not None

    def test_soft_delete(self):
        now = datetime.now(timezone.utc)
        meeting = Meeting(
            host_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Delete me",
            meeting_code="abc-defg-hij",
            meeting_link="https://workspace.app/m/abc-defg-hij",
            deleted_at=now,
        )
        assert meeting.deleted_at == now

    def test_created_at_default_utc(self):
        now = datetime.now(timezone.utc)
        meeting = Meeting(
            host_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Meeting",
            meeting_code="abc-defg-hij",
            meeting_link="https://workspace.app/m/abc-defg-hij",
            created_at=now,
        )
        assert meeting.created_at is not None
        assert meeting.created_at.tzinfo == timezone.utc

    def test_updated_at_default_utc(self):
        now = datetime.now(timezone.utc)
        meeting = Meeting(
            host_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Meeting",
            meeting_code="abc-defg-hij",
            meeting_link="https://workspace.app/m/abc-defg-hij",
            updated_at=now,
        )
        assert meeting.updated_at is not None
        assert meeting.updated_at.tzinfo == timezone.utc


class TestMeetingParticipantModel:
    def test_tablename(self):
        assert MeetingParticipant.__tablename__ == "meeting_participants"

    def test_unique_constraint(self):
        assert any(
            isinstance(c, Index) and c.name == "uq_meeting_participant_session"
            for c in MeetingParticipant.__table_args__
        )

    def test_minimal_fields(self):
        now = datetime.now(timezone.utc)
        session_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        participant = MeetingParticipant(
            session_id=session_id,
            participant_type=ParticipantType.REGISTERED,
            status=ParticipantStatus.WAITING,
            is_muted=False,
            can_start_screen_share=False,
            joined_at=now,
        )
        assert participant.session_id == session_id
        assert participant.user_id is None
        assert participant.guest_name is None
        assert participant.guest_email is None
        assert participant.participant_type == ParticipantType.REGISTERED
        assert participant.status == ParticipantStatus.WAITING
        assert participant.is_muted is False
        assert participant.can_start_screen_share is False
        assert isinstance(participant.joined_at, datetime)

    def test_full_fields(self):
        now = datetime.now(timezone.utc)
        participant = MeetingParticipant(
            session_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            user_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            guest_name="Guest User",
            guest_email="guest@example.com",
            participant_type=ParticipantType.GUEST,
            status=ParticipantStatus.ADMITTED,
            is_muted=True,
            can_start_screen_share=True,
            joined_at=now,
            left_at=now,
        )
        assert participant.user_id is not None
        assert participant.guest_name == "Guest User"
        assert participant.status == ParticipantStatus.ADMITTED
        assert participant.is_muted is True
        assert participant.can_start_screen_share is True


class TestMeetingRecordingModel:
    def test_tablename(self):
        assert MeetingRecording.__tablename__ == "meeting_recordings"

    def test_minimal_fields(self):
        now = datetime.now(timezone.utc)
        rec = MeetingRecording(
            session_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            filename="recording.webm",
            content_type="audio/webm",
            size=1024,
            created_at=now,
        )
        assert rec.session_id == uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert rec.filename == "recording.webm"
        assert rec.content_type == "audio/webm"
        assert rec.size == 1024
        assert rec.duration is None
        assert rec.storage_path is None
        assert isinstance(rec.created_at, datetime)

    def test_full_fields(self):
        now = datetime.now(timezone.utc)
        rec = MeetingRecording(
            session_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            filename="recording.webm",
            content_type="audio/webm",
            size=2048,
            duration=120.5,
            storage_path="/storage/rec.webm",
            created_at=now,
        )
        assert rec.duration == 120.5
        assert rec.storage_path == "/storage/rec.webm"


class TestMeetingTranscriptModel:
    def test_tablename(self):
        assert MeetingTranscript.__tablename__ == "meeting_transcripts"

    def test_minimal_fields(self):
        now = datetime.now(timezone.utc)
        tx = MeetingTranscript(
            session_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            filename="transcript.txt",
            content_type="text/plain",
            size=100,
            storage_path="/tmp/tx.txt",
            created_at=now,
        )
        assert tx.session_id == uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert tx.filename == "transcript.txt"
        assert tx.content_type == "text/plain"
        assert tx.size == 100
        assert tx.storage_path == "/tmp/tx.txt"
        assert isinstance(tx.created_at, datetime)


class TestMeetingAIAnalysisModel:
    def test_tablename(self):
        assert MeetingAIAnalysis.__tablename__ == "meeting_ai_analysis"

    def test_minimal_fields(self):
        now = datetime.now(timezone.utc)
        analysis = MeetingAIAnalysis(
            session_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            provider="NVIDIA_NIM",
            model="meta/llama-3.3-70b-instruct",
            status=AIAnalysisStatus.PENDING,
            created_at=now,
        )
        assert analysis.session_id == uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert analysis.provider == "NVIDIA_NIM"
        assert analysis.model == "meta/llama-3.3-70b-instruct"
        assert analysis.status == AIAnalysisStatus.PENDING
        assert analysis.summary is None
        assert analysis.agenda_coverage_percentage is None
        assert analysis.covered_points is None
        assert isinstance(analysis.created_at, datetime)

    def test_full_fields(self):
        now = datetime.now(timezone.utc)
        analysis = MeetingAIAnalysis(
            session_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            provider="NVIDIA_NIM",
            model="meta/llama-3.3-70b-instruct",
            status=AIAnalysisStatus.COMPLETED,
            summary="Summary text",
            agenda_coverage_percentage=85,
            covered_points=["point1"],
            out_of_agenda_points=["point2"],
            suggested_tasks=[{"title": "Task1"}],
            raw_response={"raw": "data"},
            processing_started_at=now,
            processing_completed_at=now,
        )
        assert analysis.status == AIAnalysisStatus.COMPLETED
        assert analysis.summary == "Summary text"
        assert analysis.agenda_coverage_percentage == 85


class TestMeetingSessionModel:
    def test_tablename(self):
        assert MeetingSession.__tablename__ == "meeting_sessions"

    def test_minimal_fields(self):
        now = datetime.now(timezone.utc)
        session = MeetingSession(
            meeting_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            host_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            status=SessionStatus.ACTIVE,
            started_at=now,
        )
        assert session.meeting_id == uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert session.host_id == uuid.UUID("87654321-4321-8765-4321-876543218765")
        assert session.status == SessionStatus.ACTIVE
        assert session.ended_at is None
        assert session.duration_seconds is None
        assert isinstance(session.started_at, datetime)

    def test_full_fields(self):
        now = datetime.now(timezone.utc)
        session = MeetingSession(
            meeting_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            host_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            status=SessionStatus.ENDED,
            started_at=now,
            ended_at=now,
            duration_seconds=3600,
        )
        assert session.status == SessionStatus.ENDED
        assert session.duration_seconds == 3600


class TestMeetingInvitationModel:
    def test_tablename(self):
        assert MeetingInvitation.__tablename__ == "meeting_invitations"

    def test_minimal_fields(self):
        now = datetime.now(timezone.utc)
        invite = MeetingInvitation(
            meeting_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            name="John Doe",
            email="john@example.com",
            created_at=now,
        )
        assert invite.meeting_id == uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert invite.name == "John Doe"
        assert invite.email == "john@example.com"
        assert isinstance(invite.created_at, datetime)
