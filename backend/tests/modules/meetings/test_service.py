import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException

from app.modules.meetings.service import MeetingService, MeetingAIAnalysisService, MeetingSessionService
from app.modules.meetings.schemas import ScheduledMeetingCreate, InvitationCreate
from app.modules.meetings.exceptions import (
    MeetingNotFoundException,
    MeetingAccessDeniedException,
    SessionAccessDeniedException,
    MeetingValidationError,
)
from app.modules.meetings.enums import (
    MeetingStatus,
    ParticipantType,
    ParticipantStatus,
    MeetingType,
    SessionStatus,
    AIAnalysisStatus,
)
from app.models.meetings import Meeting, MeetingParticipant, MeetingSession
from app.core.config import Settings
from app.modules.meetings.repository import MeetingSessionRepository, MeetingRepository, MeetingAIAnalysisRepository
from app.modules.meetings.ai_provider_service import AIProviderService


def _make_mock_settings():
    settings = MagicMock(spec=Settings)
    settings.JWT_SECRET_KEY = "test_secret"
    settings.MEETING_SESSION_TOKEN_EXPIRE_MINUTES = 60
    settings.FRONTEND_URL = "https://example.com"
    settings.NVIDIA_NIM_API_KEY = "test_nim_key"
    settings.NVIDIA_NIM_TIMEOUT = 300
    return settings


def _make_mock_repo():
    repo = AsyncMock()
    return repo


def _make_mock_storage():
    storage = MagicMock()
    storage.save_recording = AsyncMock(return_value={"filename": "r.webm", "storage_path": "/tmp/r.webm", "size": 1024})
    storage.save_transcript = AsyncMock(return_value={"filename": "t.txt", "storage_path": "/tmp/t.txt", "size": 2048})
    storage.exists = MagicMock(return_value=True)
    storage.delete_file = AsyncMock(return_value=True)
    return storage


def _make_mock_session_service():
    svc = AsyncMock(spec=MeetingSessionService)
    svc.repo = AsyncMock(spec=MeetingSessionRepository)
    return svc


def _make_mock_auth_service():
    svc = AsyncMock()
    return svc


class TestMeetingService:
    @pytest.fixture
    def repo(self):
        return _make_mock_repo()

    @pytest.fixture
    def storage(self):
        return _make_mock_storage()

    @pytest.fixture
    def session_service(self):
        return _make_mock_session_service()

    @pytest.fixture
    def auth_service(self):
        return _make_mock_auth_service()

    @pytest.fixture
    def service(self, repo, storage, session_service, auth_service):
        return MeetingService(repo, storage, session_service, auth_service)

    def _make_meeting(self, host_id=None, status=MeetingStatus.CREATED, meeting_type=MeetingType.INSTANT, active_screen_sharer_id=None):
        return MagicMock(
            spec=Meeting,
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            host_id=host_id or uuid.UUID("87654321-4321-8765-4321-876543218765"),
            title="Test Meeting",
            status=status,
            meeting_type=meeting_type,
            active_screen_sharer_id=active_screen_sharer_id,
            ended_at=None,
            deleted_at=None,
        )

    async def test_create_meeting(self, service, repo):
        host_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        repo.create.return_value = self._make_meeting(host_id=host_id)
        payload = MagicMock()
        payload.model_dump.return_value = {"title": "New Meeting"}
        result = await service.create_meeting(host_id, payload)
        assert result.host_id == host_id
        repo.create.assert_called_once_with(host_id, {"title": "New Meeting"})

    async def test_get_meeting_success(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        repo.count_invitations.return_value = 0
        result = await service.get_meeting(meeting.id)
        assert result.host_id == meeting.host_id

    async def test_get_meeting_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(MeetingNotFoundException):
            await service.get_meeting(uuid.UUID("12345678-1234-5678-1234-567812345678"))

    async def test_update_meeting_success(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        user_id = meeting.host_id
        repo.update.return_value = meeting
        payload = MagicMock()
        payload.model_dump.return_value = {"title": "Updated"}
        result = await service.update_meeting(user_id, meeting.id, payload)
        assert result == meeting
        repo.update.assert_called_once()

    async def test_update_meeting_access_denied(self, service, repo):
        meeting = self._make_meeting(host_id=uuid.UUID("87654321-4321-8765-4321-876543218765"))
        repo.get_by_id.return_value = meeting
        bad_user = uuid.UUID("11111111-1111-1111-1111-111111111111")
        with pytest.raises(MeetingAccessDeniedException):
            await service.update_meeting(bad_user, meeting.id, MagicMock())

    async def test_update_meeting_cancelled_raises(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.CANCELLED)
        repo.get_by_id.return_value = meeting
        with pytest.raises(MeetingValidationError, match="already been cancelled"):
            await service.update_meeting(meeting.host_id, meeting.id, MagicMock())

    async def test_update_meeting_ended_raises(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.ENDED)
        repo.get_by_id.return_value = meeting
        with pytest.raises(MeetingValidationError, match="already been ended"):
            await service.update_meeting(meeting.host_id, meeting.id, MagicMock())

    async def test_list_meetings(self, service, repo):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        meetings = [self._make_meeting()]
        repo.list_user_meetings.return_value = meetings
        result = await service.list_meetings(user_id)
        assert len(result) == 1
        repo.list_user_meetings.assert_called_once_with(user_id)

    async def test_end_meeting_success(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.ACTIVE)
        repo.get_by_id.return_value = meeting
        repo.get_participants_list.return_value = []
        service.session_service.get_active_session.return_value = None
        updated_meeting = self._make_meeting(status=MeetingStatus.IDLE)
        repo.update.return_value = updated_meeting
        with patch.object(service, "_trigger_completion_pipeline", new_callable=AsyncMock):
            result = await service.end_meeting(meeting.host_id, meeting.id)
        assert result.status in (MeetingStatus.ENDED, MeetingStatus.IDLE)

    async def test_end_meeting_not_active_raises(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.CREATED)
        repo.get_by_id.return_value = meeting
        with pytest.raises(MeetingValidationError, match="Only active or idle"):
            await service.end_meeting(meeting.host_id, meeting.id)

    async def test_cancel_meeting_success(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.SCHEDULED)
        repo.get_by_id.return_value = meeting
        service.session_service.get_active_session.return_value = None
        cancelled_meeting = self._make_meeting(status=MeetingStatus.CANCELLED)
        repo.update.return_value = cancelled_meeting
        result = await service.cancel_meeting(meeting.host_id, meeting.id)
        assert result.status == MeetingStatus.CANCELLED

    async def test_cancel_meeting_already_cancelled_raises(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.CANCELLED)
        repo.get_by_id.return_value = meeting
        with pytest.raises(MeetingValidationError, match="already been cancelled"):
            await service.cancel_meeting(meeting.host_id, meeting.id)

    async def test_cancel_meeting_already_ended_raises(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.ENDED)
        repo.get_by_id.return_value = meeting
        with pytest.raises(MeetingValidationError, match="Cannot cancel a meeting that has already ended"):
            await service.cancel_meeting(meeting.host_id, meeting.id)

    async def test_delete_meeting_success(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        el_repo = AsyncMock()
        with patch("app.modules.meetings.service.EntityLinkRepository", return_value=el_repo):
            result = await service.delete_meeting(meeting.host_id, meeting.id)
        assert result == meeting
        repo.soft_delete.assert_called_with(meeting)

    async def test_get_meeting_by_code_success(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_code.return_value = meeting
        repo.get_user_name_by_id.return_value = "Host Name"
        repo.count_invitations.return_value = 0
        result = await service.get_meeting_by_code("abc-defg-hij")
        assert result[0] == meeting
        assert result[1] == "Host Name"

    async def test_join_meeting_flow_guest_email_required(self, service, repo):
        repo.get_by_id.return_value = self._make_meeting()
        with pytest.raises(MeetingValidationError, match="Guest email is required"):
            await service.join_meeting_flow(
                uuid.UUID("12345678-1234-5678-1234-567812345678"),
                user_id=None,
                guest_email=None,
            )

    async def test_generate_meeting_session_token(self):
        participant_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        meeting_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        with patch("app.modules.meetings.service.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "secret"
            mock_settings.MEETING_SESSION_TOKEN_EXPIRE_MINUTES = 60
            token = MeetingService.generate_meeting_session_token(participant_id, meeting_id)
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])
        assert decoded["participant_id"] == str(participant_id)
        assert decoded["meeting_id"] == str(meeting_id)
        assert "exp" in decoded

    async def test_toggle_participant_mute_host_only(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        participant = MagicMock(spec=MeetingParticipant, id=uuid.uuid4(), status=ParticipantStatus.ADMITTED)
        repo.get_participant_by_id.return_value = participant
        bad_user = uuid.UUID("11111111-1111-1111-1111-111111111111")
        with pytest.raises(MeetingAccessDeniedException):
            await service.toggle_participant_mute(bad_user, meeting.id, participant.id, mute=True)

    async def test_request_screen_share_not_active_raises(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.CREATED)
        repo.get_by_id.return_value = meeting
        with pytest.raises(MeetingValidationError, match="Meeting is not active"):
            await service.request_screen_share(meeting.id, uuid.uuid4())

    async def test_start_screen_share_already_sharing_raises(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.ACTIVE, active_screen_sharer_id=uuid.uuid4())
        repo.get_by_id.return_value = meeting
        with pytest.raises(MeetingValidationError, match="already sharing"):
            await service.start_screen_share(meeting.id, uuid.uuid4(), user_id=meeting.host_id)

    async def test_stop_screen_share_not_sharer_raises(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.ACTIVE, active_screen_sharer_id=uuid.uuid4())
        repo.get_by_id.return_value = meeting
        bad_participant = uuid.UUID("11111111-1111-1111-1111-111111111111")
        with pytest.raises(MeetingValidationError, match="not the active screen sharer"):
            await service.stop_screen_share(meeting.id, bad_participant)

    async def test_leave_meeting_no_active_session(self, service, repo):
        service.session_service.get_active_session.return_value = None
        with pytest.raises(MeetingValidationError, match="No active session"):
            await service.leave_meeting(uuid.UUID("12345678-1234-5678-1234-567812345678"), user_id=uuid.uuid4())

    async def test_get_waiting_count(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        waiting = [MagicMock(status=ParticipantStatus.WAITING), MagicMock(status=ParticipantStatus.ADMITTED)]
        repo.get_participants_by_meeting.return_value = waiting
        count = await service.get_waiting_count(meeting.id)
        assert count == 1

    # --- leave_meeting_flow ---
    async def test_leave_meeting_flow_no_active_session(self, service, repo):
        service.session_service.get_active_session.return_value = None
        result = await service.leave_meeting_flow(
            uuid.UUID("12345678-1234-5678-1234-567812345678"),
            user_id=uuid.uuid4()
        )
        assert result is None

    async def test_leave_meeting_flow_success(self, service, repo):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        participant_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        session = MagicMock(id=uuid.uuid4())
        service.session_service.get_active_session.return_value = session
        participant = MagicMock(id=participant_id, status=ParticipantStatus.ADMITTED)
        repo.get_active_participant.return_value = participant
        repo.get_participants_by_meeting.return_value = []
        result = await service.leave_meeting_flow(meeting_id, user_id=uuid.uuid4())
        repo.update_participant.assert_called_once()
        update_dict = repo.update_participant.call_args[0][1]
        assert update_dict["status"] == ParticipantStatus.LEFT

    # --- list_participants ---
    async def test_list_participants_host(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        repo.get_participants_by_meeting.return_value = [MagicMock(), MagicMock()]
        result = await service.list_participants(meeting.id, user_id=meeting.host_id)
        assert len(result) == 2

    async def test_list_participants_non_host_with_access(self, service, repo):
        meeting = self._make_meeting()
        user_id = uuid.uuid4()
        repo.get_by_id.return_value = meeting
        service.auth_service.get_accessible_session_ids.return_value = [uuid.uuid4()]
        repo.get_participants_by_session_ids.return_value = [MagicMock()]
        result = await service.list_participants(meeting.id, user_id=user_id)
        assert len(result) == 1

    async def test_list_participants_non_host_no_access(self, service, repo):
        meeting = self._make_meeting()
        user_id = uuid.uuid4()
        repo.get_by_id.return_value = meeting
        service.auth_service.get_accessible_session_ids.return_value = []
        result = await service.list_participants(meeting.id, user_id=user_id)
        assert result == []

    async def test_list_participants_no_user_id(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        result = await service.list_participants(meeting.id, user_id=None)
        assert result == []

    # --- save_recording_file ---
    async def test_save_recording_file_success(self, service, repo, storage):
        meeting = self._make_meeting(status=MeetingStatus.ACTIVE)
        repo.get_by_id.return_value = meeting
        session = MagicMock(id=uuid.uuid4())
        service.session_service.get_active_session.return_value = session
        service.auth_service.verify_session_access = AsyncMock()
        file = AsyncMock()
        file.read.return_value = b"recording content"
        file.content_type = "audio/webm"
        file.filename = "recording.webm"
        repo.add_recording.return_value = MagicMock()
        result = await service.save_recording_file(meeting.id, uuid.uuid4(), file, duration=120.0)
        repo.add_recording.assert_called_once()
        assert result == repo.add_recording.return_value

    async def test_save_recording_file_no_active_session(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.ACTIVE)
        repo.get_by_id.return_value = meeting
        service.session_service.get_active_session.return_value = None
        file = AsyncMock()
        with pytest.raises(MeetingValidationError, match="No active session"):
            await service.save_recording_file(meeting.id, uuid.uuid4(), file, None)

    async def test_save_recording_file_no_filename(self, service, repo, storage):
        meeting = self._make_meeting(status=MeetingStatus.ACTIVE)
        repo.get_by_id.return_value = meeting
        session = MagicMock(id=uuid.uuid4())
        service.session_service.get_active_session.return_value = session
        service.auth_service.verify_session_access = AsyncMock()
        file = AsyncMock()
        file.read.return_value = b"content"
        file.content_type = "audio/webm"
        file.filename = None
        repo.add_recording.return_value = MagicMock()
        result = await service.save_recording_file(meeting.id, uuid.uuid4(), file, None)
        assert result is not None

    # --- save_transcript_file ---
    async def test_save_transcript_file_success(self, service, repo, storage):
        meeting = self._make_meeting(status=MeetingStatus.ACTIVE)
        repo.get_by_id.return_value = meeting
        session = MagicMock(id=uuid.uuid4())
        service.session_service.get_active_session.return_value = session
        service.auth_service.verify_session_access = AsyncMock()
        file = AsyncMock()
        file.read.return_value = b"transcript content"
        file.filename = "transcript.txt"
        repo.add_transcript.return_value = MagicMock()
        result = await service.save_transcript_file(meeting.id, uuid.uuid4(), file)
        repo.add_transcript.assert_called_once()
        assert result == repo.add_transcript.return_value

    async def test_save_transcript_file_no_active_session(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.ACTIVE)
        repo.get_by_id.return_value = meeting
        service.session_service.get_active_session.return_value = None
        file = AsyncMock()
        with pytest.raises(MeetingValidationError, match="No active session"):
            await service.save_transcript_file(meeting.id, uuid.uuid4(), file)

    # --- get_recording_artifact ---
    async def test_get_recording_artifact_success(self, service, repo, storage):
        rec = MagicMock(storage_path="/tmp/rec.webm")
        repo.get_recording_by_id.return_value = rec
        storage.exists.return_value = True
        session = MagicMock(id=uuid.uuid4(), meeting_id=uuid.uuid4())
        repo.get_session_by_recording_id.return_value = session
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        service.auth_service.verify_session_access = AsyncMock()
        result = await service.get_recording_artifact(uuid.uuid4(), user_id=uuid.uuid4())
        assert result == rec

    async def test_get_recording_artifact_not_found(self, service, repo, storage):
        repo.get_recording_by_id.return_value = None
        with pytest.raises(MeetingNotFoundException):
            await service.get_recording_artifact(uuid.uuid4(), user_id=uuid.uuid4())

    async def test_get_recording_artifact_no_storage(self, service, repo, storage):
        repo.get_recording_by_id.return_value = MagicMock(storage_path="/tmp/rec.webm")
        storage.exists.return_value = False
        with pytest.raises(MeetingNotFoundException):
            await service.get_recording_artifact(uuid.uuid4(), user_id=uuid.uuid4())

    async def test_get_recording_artifact_no_session(self, service, repo, storage):
        repo.get_recording_by_id.return_value = MagicMock(storage_path="/tmp/rec.webm")
        storage.exists.return_value = True
        repo.get_session_by_recording_id.return_value = None
        with pytest.raises(MeetingNotFoundException):
            await service.get_recording_artifact(uuid.uuid4(), user_id=uuid.uuid4())

    # --- get_transcript_artifact ---
    async def test_get_transcript_artifact_success(self, service, repo, storage):
        tx = MagicMock(storage_path="/tmp/tx.txt")
        repo.get_transcript_by_id.return_value = tx
        storage.exists.return_value = True
        session = MagicMock(id=uuid.uuid4(), meeting_id=uuid.uuid4())
        repo.get_session_by_transcript_id.return_value = session
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        service.auth_service.verify_session_access = AsyncMock()
        result = await service.get_transcript_artifact(uuid.uuid4(), user_id=uuid.uuid4())
        assert result == tx

    async def test_get_transcript_artifact_not_found(self, service, repo, storage):
        repo.get_transcript_by_id.return_value = None
        with pytest.raises(MeetingNotFoundException):
            await service.get_transcript_artifact(uuid.uuid4(), user_id=uuid.uuid4())

    # --- list_recordings ---
    async def test_list_recordings_host(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        repo.list_recordings_by_meeting.return_value = [MagicMock(), MagicMock()]
        result = await service.list_recordings(meeting.id, user_id=meeting.host_id)
        assert len(result) == 2

    async def test_list_recordings_non_host_with_access(self, service, repo):
        meeting = self._make_meeting()
        user_id = uuid.uuid4()
        repo.get_by_id.return_value = meeting
        service.auth_service.get_accessible_session_ids.return_value = [uuid.uuid4()]
        repo.list_recordings_by_session_ids.return_value = [MagicMock()]
        result = await service.list_recordings(meeting.id, user_id=user_id)
        assert len(result) == 1

    async def test_list_recordings_non_host_no_access(self, service, repo):
        meeting = self._make_meeting()
        user_id = uuid.uuid4()
        repo.get_by_id.return_value = meeting
        service.auth_service.get_accessible_session_ids.return_value = []
        result = await service.list_recordings(meeting.id, user_id=user_id)
        assert result == []

    # --- list_transcripts ---
    async def test_list_transcripts_host(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        repo.list_transcripts_by_meeting.return_value = [MagicMock()]
        result = await service.list_transcripts(meeting.id, user_id=meeting.host_id)
        assert len(result) == 1

    async def test_list_transcripts_non_host_no_access(self, service, repo):
        meeting = self._make_meeting()
        user_id = uuid.uuid4()
        repo.get_by_id.return_value = meeting
        service.auth_service.get_accessible_session_ids.return_value = []
        result = await service.list_transcripts(meeting.id, user_id=user_id)
        assert result == []

    # --- remove_recording ---
    async def test_remove_recording_success(self, service, repo, storage):
        rec = MagicMock(storage_path="/tmp/rec.webm", id=uuid.uuid4())
        repo.get_recording_by_id.return_value = rec
        meeting = self._make_meeting()
        repo.get_meeting_by_recording_id.return_value = meeting
        await service.remove_recording(rec.id, user_id=meeting.host_id)
        storage.delete_file.assert_called_once_with(rec.storage_path)
        repo.delete_recording_meta.assert_called_once_with(rec)

    async def test_remove_recording_not_found(self, service, repo):
        repo.get_recording_by_id.return_value = None
        result = await service.remove_recording(uuid.uuid4(), user_id=uuid.uuid4())
        assert result is None

    async def test_remove_recording_no_meeting(self, service, repo):
        rec = MagicMock(storage_path="/tmp/rec.webm", id=uuid.uuid4())
        repo.get_recording_by_id.return_value = rec
        repo.get_meeting_by_recording_id.return_value = None
        with pytest.raises(MeetingNotFoundException):
            await service.remove_recording(rec.id, user_id=uuid.uuid4())

    async def test_remove_recording_access_denied(self, service, repo):
        rec = MagicMock(storage_path="/tmp/rec.webm", id=uuid.uuid4())
        repo.get_recording_by_id.return_value = rec
        meeting = self._make_meeting()
        repo.get_meeting_by_recording_id.return_value = meeting
        bad_user = uuid.UUID("11111111-1111-1111-1111-111111111111")
        with pytest.raises(MeetingAccessDeniedException):
            await service.remove_recording(rec.id, user_id=bad_user)

    # --- remove_transcript ---
    async def test_remove_transcript_success(self, service, repo, storage):
        tx = MagicMock(storage_path="/tmp/tx.txt", id=uuid.uuid4())
        repo.get_transcript_by_id.return_value = tx
        meeting = self._make_meeting()
        repo.get_meeting_by_transcript_id.return_value = meeting
        await service.remove_transcript(tx.id, user_id=meeting.host_id)
        storage.delete_file.assert_called_once_with(tx.storage_path)
        repo.delete_transcript_meta.assert_called_once_with(tx)

    async def test_remove_transcript_not_found(self, service, repo):
        repo.get_transcript_by_id.return_value = None
        result = await service.remove_transcript(uuid.uuid4(), user_id=uuid.uuid4())
        assert result is None

    async def test_remove_transcript_access_denied(self, service, repo):
        tx = MagicMock(storage_path="/tmp/tx.txt", id=uuid.uuid4())
        repo.get_transcript_by_id.return_value = tx
        meeting = self._make_meeting()
        repo.get_meeting_by_transcript_id.return_value = meeting
        bad_user = uuid.UUID("11111111-1111-1111-1111-111111111111")
        with pytest.raises(MeetingAccessDeniedException):
            await service.remove_transcript(tx.id, user_id=bad_user)

    # --- update_participant_status ---
    async def test_update_participant_status_admit_from_waiting(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        participant = MagicMock(
            id=uuid.uuid4(), session_id=uuid.uuid4(),
            status=ParticipantStatus.WAITING
        )
        repo.get_participant_by_id.return_value = participant
        session = MagicMock(meeting_id=meeting.id)
        service.session_service.repo.get_by_id.return_value = session
        result = await service.update_participant_status(
            meeting.host_id, meeting.id, participant.id, ParticipantStatus.ADMITTED
        )
        assert result == repo.update_participant.return_value

    async def test_update_participant_status_already_admitted(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        participant = MagicMock(
            id=uuid.uuid4(), session_id=uuid.uuid4(),
            status=ParticipantStatus.ADMITTED
        )
        repo.get_participant_by_id.return_value = participant
        session = MagicMock(meeting_id=meeting.id)
        service.session_service.repo.get_by_id.return_value = session
        result = await service.update_participant_status(
            meeting.host_id, meeting.id, participant.id, ParticipantStatus.ADMITTED
        )
        assert result == participant

    async def test_update_participant_status_reject_not_waiting(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        participant = MagicMock(
            id=uuid.uuid4(), session_id=uuid.uuid4(),
            status=ParticipantStatus.ADMITTED
        )
        repo.get_participant_by_id.return_value = participant
        session = MagicMock(meeting_id=meeting.id)
        service.session_service.repo.get_by_id.return_value = session
        with pytest.raises(MeetingValidationError, match="Can only reject participants who are waiting"):
            await service.update_participant_status(
                meeting.host_id, meeting.id, participant.id, ParticipantStatus.REJECTED
            )

    async def test_update_participant_status_remove_not_admitted(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        participant = MagicMock(
            id=uuid.uuid4(), session_id=uuid.uuid4(),
            status=ParticipantStatus.WAITING
        )
        repo.get_participant_by_id.return_value = participant
        session = MagicMock(meeting_id=meeting.id)
        service.session_service.repo.get_by_id.return_value = session
        with pytest.raises(MeetingValidationError, match="Can only remove admitted participants"):
            await service.update_participant_status(
                meeting.host_id, meeting.id, participant.id, ParticipantStatus.REMOVED
            )

    async def test_update_participant_status_admit_not_waiting(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        participant = MagicMock(
            id=uuid.uuid4(), session_id=uuid.uuid4(),
            status=ParticipantStatus.LEFT
        )
        repo.get_participant_by_id.return_value = participant
        session = MagicMock(meeting_id=meeting.id)
        service.session_service.repo.get_by_id.return_value = session
        with pytest.raises(MeetingValidationError, match="Can only admit participants who are waiting"):
            await service.update_participant_status(
                meeting.host_id, meeting.id, participant.id, ParticipantStatus.ADMITTED
            )

    async def test_update_participant_status_access_denied(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        bad_user = uuid.UUID("11111111-1111-1111-1111-111111111111")
        with pytest.raises(MeetingAccessDeniedException):
            await service.update_participant_status(
                bad_user, meeting.id, uuid.uuid4(), ParticipantStatus.ADMITTED
            )

    async def test_update_participant_status_removed_clears_screen_sharer(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        participant_id = uuid.uuid4()
        participant = MagicMock(
            id=participant_id, session_id=uuid.uuid4(),
            status=ParticipantStatus.ADMITTED
        )
        repo.get_participant_by_id.return_value = participant
        session = MagicMock(meeting_id=meeting.id)
        service.session_service.repo.get_by_id.return_value = session
        result = await service.update_participant_status(
            meeting.host_id, meeting.id, participant_id, ParticipantStatus.REMOVED
        )
        assert result is not None

    # --- toggle_participant_mute ---
    async def test_toggle_participant_mute_success(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        participant = MagicMock(id=uuid.uuid4(), session_id=uuid.uuid4(), status=ParticipantStatus.ADMITTED)
        repo.get_participant_by_id.return_value = participant
        session = MagicMock(meeting_id=meeting.id)
        service.session_service.repo.get_by_id.return_value = session
        result = await service.toggle_participant_mute(meeting.host_id, meeting.id, participant.id, mute=True)
        repo.update_participant.assert_called_once()
        assert result is not None

    # --- approve_screen_share ---
    async def test_approve_screen_share_success(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        participant = MagicMock(id=uuid.uuid4(), session_id=uuid.uuid4())
        repo.get_participant_by_id.return_value = participant
        session = MagicMock(meeting_id=meeting.id)
        service.session_service.repo.get_by_id.return_value = session
        result = await service.approve_screen_share(meeting.id, meeting.host_id, participant.id)
        repo.update_participant.assert_called_once_with(participant, {"can_start_screen_share": True})
        assert result is not None

    async def test_approve_screen_share_access_denied(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        bad_user = uuid.UUID("11111111-1111-1111-1111-111111111111")
        with pytest.raises(MeetingAccessDeniedException):
            await service.approve_screen_share(meeting.id, bad_user, uuid.uuid4())

    # --- reject_screen_share ---
    async def test_reject_screen_share_success(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        participant = MagicMock(id=uuid.uuid4(), session_id=uuid.uuid4())
        repo.get_participant_by_id.return_value = participant
        session = MagicMock(meeting_id=meeting.id)
        service.session_service.repo.get_by_id.return_value = session
        result = await service.reject_screen_share(meeting.id, meeting.host_id, participant.id)
        assert result == participant

    async def test_reject_screen_share_access_denied(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        bad_user = uuid.UUID("11111111-1111-1111-1111-111111111111")
        with pytest.raises(MeetingAccessDeniedException):
            await service.reject_screen_share(meeting.id, bad_user, uuid.uuid4())

    # --- start_screen_share ---
    async def test_start_screen_share_success(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.ACTIVE, active_screen_sharer_id=None)
        repo.get_by_id.return_value = meeting
        participant = MagicMock(id=uuid.uuid4(), can_start_screen_share=True)
        repo.get_participant_by_id.return_value = participant
        session = MagicMock(meeting_id=meeting.id)
        service.session_service.repo.get_by_id.return_value = session
        result = await service.start_screen_share(meeting.id, participant.id, user_id=meeting.host_id)
        repo.update.assert_called_once_with(meeting, {"active_screen_sharer_id": participant.id})

    async def test_start_screen_share_not_active(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.CREATED)
        repo.get_by_id.return_value = meeting
        with pytest.raises(MeetingValidationError, match="Meeting is not active"):
            await service.start_screen_share(meeting.id, uuid.uuid4())

    async def test_start_screen_share_no_permission(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.ACTIVE, active_screen_sharer_id=None)
        repo.get_by_id.return_value = meeting
        participant = MagicMock(id=uuid.uuid4(), session_id=uuid.uuid4(), can_start_screen_share=False)
        repo.get_participant_by_id.return_value = participant
        session = MagicMock(meeting_id=meeting.id)
        service.session_service.repo.get_by_id.return_value = session
        with pytest.raises(MeetingValidationError, match="do not have permission"):
            await service.start_screen_share(meeting.id, participant.id, user_id=None)

    # --- stop_screen_share ---
    async def test_stop_screen_share_success(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.ACTIVE, active_screen_sharer_id=uuid.uuid4())
        repo.get_by_id.return_value = meeting
        result = await service.stop_screen_share(meeting.id, meeting.active_screen_sharer_id)
        repo.update.assert_called_once_with(meeting, {"active_screen_sharer_id": None})

    # --- force_stop_screen_share ---
    async def test_force_stop_screen_share_success(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.ACTIVE, active_screen_sharer_id=uuid.uuid4())
        repo.get_by_id.return_value = meeting
        result = await service.force_stop_screen_share(meeting.id, meeting.host_id)
        repo.update.assert_called_once_with(meeting, {"active_screen_sharer_id": None})

    async def test_force_stop_screen_share_access_denied(self, service, repo):
        meeting = self._make_meeting(active_screen_sharer_id=uuid.uuid4())
        repo.get_by_id.return_value = meeting
        bad_user = uuid.UUID("11111111-1111-1111-1111-111111111111")
        with pytest.raises(MeetingAccessDeniedException):
            await service.force_stop_screen_share(meeting.id, bad_user)

    # --- request_screen_share ---
    async def test_request_screen_share_not_admitted(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.ACTIVE)
        repo.get_by_id.return_value = meeting
        participant = MagicMock(
            id=uuid.uuid4(), session_id=uuid.uuid4(),
            status=ParticipantStatus.WAITING,
            can_start_screen_share=False
        )
        repo.get_participant_by_id.return_value = participant
        session = MagicMock(meeting_id=meeting.id)
        service.session_service.repo.get_by_id.return_value = session
        with pytest.raises(MeetingValidationError, match="Participant must be admitted"):
            await service.request_screen_share(meeting.id, participant.id)

    async def test_request_screen_share_already_has_permission(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.ACTIVE)
        repo.get_by_id.return_value = meeting
        participant = MagicMock(
            id=uuid.uuid4(), session_id=uuid.uuid4(),
            status=ParticipantStatus.ADMITTED,
            can_start_screen_share=True
        )
        repo.get_participant_by_id.return_value = participant
        session = MagicMock(meeting_id=meeting.id)
        service.session_service.repo.get_by_id.return_value = session
        with pytest.raises(MeetingValidationError, match="already granted"):
            await service.request_screen_share(meeting.id, participant.id)

    async def test_request_screen_share_success(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.ACTIVE)
        repo.get_by_id.return_value = meeting
        participant = MagicMock(
            id=uuid.uuid4(), session_id=uuid.uuid4(),
            status=ParticipantStatus.ADMITTED,
            can_start_screen_share=False
        )
        repo.get_participant_by_id.return_value = participant
        session = MagicMock(meeting_id=meeting.id)
        service.session_service.repo.get_by_id.return_value = session
        result = await service.request_screen_share(meeting.id, participant.id)
        assert result == participant

    # --- leave_meeting ---
    async def test_leave_meeting_success(self, service, repo):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        session = MagicMock(id=uuid.uuid4())
        service.session_service.get_active_session.return_value = session
        participant = MagicMock(id=uuid.uuid4(), status=ParticipantStatus.ADMITTED)
        repo.get_active_participant.return_value = participant
        repo.get_participants_by_meeting.return_value = []
        result = await service.leave_meeting(meeting_id, user_id=uuid.uuid4())
        repo.update_participant.assert_called_once()
        assert result == repo.update_participant.return_value

    async def test_leave_meeting_waiting_raises(self, service, repo):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        session = MagicMock(id=uuid.uuid4())
        service.session_service.get_active_session.return_value = session
        participant = MagicMock(id=uuid.uuid4(), status=ParticipantStatus.WAITING)
        repo.get_active_participant.return_value = participant
        with pytest.raises(MeetingValidationError, match="not been admitted"):
            await service.leave_meeting(meeting_id, user_id=uuid.uuid4())

    async def test_leave_meeting_participant_not_found(self, service, repo):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        session = MagicMock(id=uuid.uuid4())
        service.session_service.get_active_session.return_value = session
        repo.get_active_participant.return_value = None
        repo.get_last_participant.return_value = None
        with pytest.raises(MeetingValidationError, match="not an active participant"):
            await service.leave_meeting(meeting_id, user_id=uuid.uuid4())

    async def test_leave_meeting_already_left(self, service, repo):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        session = MagicMock(id=uuid.uuid4())
        service.session_service.get_active_session.return_value = session
        repo.get_active_participant.return_value = None
        last = MagicMock(id=uuid.uuid4(), status=ParticipantStatus.LEFT)
        repo.get_last_participant.return_value = last
        result = await service.leave_meeting(meeting_id, user_id=uuid.uuid4())
        assert result == last

    # --- _transition_to_idle_if_empty ---
    async def test_transition_to_idle_if_empty_transitions(self, service, repo):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        repo.get_participants_by_meeting.return_value = []
        meeting = self._make_meeting(status=MeetingStatus.ACTIVE)
        repo.get_by_id.return_value = meeting
        await service._transition_to_idle_if_empty(meeting_id)
        repo.update.assert_called_once_with(meeting, {"status": MeetingStatus.IDLE})

    async def test_transition_to_idle_if_empty_has_participants(self, service, repo):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        repo.get_participants_by_meeting.return_value = [MagicMock()]
        await service._transition_to_idle_if_empty(meeting_id)
        repo.update.assert_not_called()

    async def test_transition_to_idle_if_empty_already_idle(self, service, repo):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        repo.get_participants_by_meeting.return_value = []
        meeting = self._make_meeting(status=MeetingStatus.IDLE)
        repo.get_by_id.return_value = meeting
        await service._transition_to_idle_if_empty(meeting_id)
        repo.update.assert_not_called()

    # --- join_meeting_flow extended ---
    async def test_join_meeting_flow_deleted_meeting(self, service, repo):
        meeting = self._make_meeting()
        meeting.deleted_at = datetime.now(timezone.utc)
        repo.get_by_id.return_value = meeting
        with pytest.raises(MeetingValidationError, match="no longer exists"):
            await service.join_meeting_flow(
                meeting.id, user_id=None, guest_email="guest@example.com"
            )

    async def test_join_meeting_flow_cancelled_meeting(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.CANCELLED)
        meeting.deleted_at = None
        repo.get_by_id.return_value = meeting
        with pytest.raises(MeetingValidationError, match="cancelled"):
            await service.join_meeting_flow(
                meeting.id, user_id=None, guest_email="guest@example.com"
            )

    async def test_join_meeting_flow_scheduled_ended(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.ENDED, meeting_type=MeetingType.SCHEDULED)
        meeting.deleted_at = None
        repo.get_by_id.return_value = meeting
        with pytest.raises(MeetingValidationError, match="ended and cannot be rejoined"):
            await service.join_meeting_flow(
                meeting.id, user_id=uuid.uuid4(), guest_email=None
            )

    async def test_join_meeting_flow_instant_reuse(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.ENDED, meeting_type=MeetingType.INSTANT)
        meeting.deleted_at = None
        repo.get_by_id.return_value = meeting
        service.session_service.get_active_session.return_value = None
        host_id = meeting.host_id
        session = MagicMock(id=uuid.uuid4())
        service.session_service.create_session.return_value = session
        repo.create_participant.return_value = MagicMock(
            id=uuid.uuid4(), user_id=host_id, guest_name=None, guest_email=None,
            participant_type=ParticipantType.REGISTERED, status=ParticipantStatus.ADMITTED,
            is_muted=False, can_start_screen_share=True, joined_at=datetime.now(timezone.utc), left_at=None
        )
        repo.get_active_participant.return_value = None
        repo.get_last_participant.return_value = None
        result = await service.join_meeting_flow(
            meeting.id, user_id=host_id, guest_email=None
        )
        assert result is not None
        repo.update.assert_called_with(meeting, {"status": MeetingStatus.ACTIVE, "ended_at": None})

    async def test_join_meeting_flow_scheduled_locked(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.SCHEDULED, meeting_type=MeetingType.SCHEDULED)
        meeting.deleted_at = None
        meeting.scheduled_start = datetime.now(timezone.utc) + timedelta(hours=2)
        repo.get_by_id.return_value = meeting
        with pytest.raises(MeetingValidationError, match="locked"):
            await service.join_meeting_flow(
                meeting.id, user_id=uuid.uuid4(), guest_email=None
            )

    async def test_join_meeting_flow_scheduled_no_invitation(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.SCHEDULED, meeting_type=MeetingType.SCHEDULED)
        meeting.deleted_at = None
        meeting.scheduled_start = datetime.now(timezone.utc) - timedelta(hours=1)
        repo.get_by_id.return_value = meeting
        repo.get_user_by_id.return_value = MagicMock(email="test@example.com")
        repo.get_invitation_by_email.return_value = None
        with pytest.raises(MeetingAccessDeniedException):
            await service.join_meeting_flow(
                meeting.id, user_id=uuid.uuid4(), guest_email=None
            )

    async def test_join_meeting_flow_guest_removed(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.ACTIVE)
        meeting.deleted_at = None
        repo.get_by_id.return_value = meeting
        session = MagicMock(id=uuid.uuid4())
        service.session_service.get_active_session.return_value = session
        existing = MagicMock(
            status=ParticipantStatus.REMOVED, id=uuid.uuid4()
        )
        repo.get_active_participant.return_value = existing
        with pytest.raises(MeetingValidationError, match="removed from this meeting"):
            await service.join_meeting_flow(
                meeting.id, user_id=None, guest_email="guest@example.com", guest_name="Guest"
            )

    async def test_join_meeting_flow_reauth_left_participant(self, service, repo):
        meeting = self._make_meeting(status=MeetingStatus.ACTIVE)
        meeting.deleted_at = None
        repo.get_by_id.return_value = meeting
        session = MagicMock(id=uuid.uuid4())
        service.session_service.get_active_session.return_value = session
        repo.get_active_participant.return_value = None
        last = MagicMock(
            id=uuid.uuid4(), status=ParticipantStatus.LEFT,
            user_id=uuid.uuid4(), guest_name=None, guest_email=None
        )
        repo.get_last_participant.return_value = last
        result = await service.join_meeting_flow(
            meeting.id, user_id=last.user_id, guest_email=None
        )
        repo.update_participant.assert_called_once()
        assert result == last

    # --- create_scheduled_meeting ---
    async def test_create_scheduled_meeting_success(self, service, repo):
        host_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_meeting = MagicMock(
            id=meeting_id, host_id=host_id,
            title="Scheduled Meeting", description="Desc",
            agenda="Agenda", meeting_type=MeetingType.SCHEDULED,
            status=MeetingStatus.SCHEDULED,
            scheduled_start=datetime.now(timezone.utc) + timedelta(days=1),
        )
        repo.create.return_value = mock_meeting
        repo.get_user_by_id.return_value = MagicMock(
            full_name="Host", email="host@example.com"
        )
        repo.create_invitation.return_value = MagicMock(
            name="Invitee", email="invitee@example.com"
        )

        payload = MagicMock(spec=ScheduledMeetingCreate)
        payload.model_dump.return_value = {
            "title": "Scheduled Meeting", "description": "Desc",
            "agenda": "Agenda", "timezone": "UTC",
            "scheduled_start": datetime.now(timezone.utc) + timedelta(days=1),
        }
        payload.scheduled_start = datetime.now(timezone.utc) + timedelta(days=1)
        payload.timezone = "UTC"
        payload.invitations = [MagicMock(name="Invitee", email="invitee@example.com")]

        with patch("app.modules.meetings.service.send_async_email") as mock_email:
            with patch("app.modules.meetings.service.settings") as mock_settings:
                mock_settings.FRONTEND_URL = "https://example.com"
                result = await service.create_scheduled_meeting(host_id, payload)
            assert result == mock_meeting
            assert mock_email.delay.call_count == 2

    async def test_create_scheduled_meeting_email_failure(self, service, repo):
        host_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_meeting = MagicMock(
            id=meeting_id, host_id=host_id,
            title="Scheduled Meeting", description="Desc",
            meeting_type=MeetingType.SCHEDULED,
            status=MeetingStatus.SCHEDULED,
            scheduled_start=datetime.now(timezone.utc) + timedelta(days=1),
        )
        repo.create.return_value = mock_meeting
        repo.get_user_by_id.return_value = MagicMock(
            full_name="Host", email="host@example.com"
        )
        repo.create_invitation.return_value = MagicMock(
            name="Invitee", email="invitee@example.com"
        )

        payload = MagicMock(spec=ScheduledMeetingCreate)
        payload.model_dump.return_value = {
            "title": "Scheduled Meeting", "timezone": "UTC",
            "scheduled_start": datetime.now(timezone.utc) + timedelta(days=1),
        }
        payload.scheduled_start = datetime.now(timezone.utc) + timedelta(days=1)
        payload.timezone = "UTC"
        payload.invitations = [MagicMock(name="Invitee", email="invitee@example.com")]

        with patch("app.modules.meetings.service.send_async_email") as mock_email:
            mock_email.delay.side_effect = Exception("Email failed")
            with patch("app.modules.meetings.service.settings") as mock_settings:
                mock_settings.FRONTEND_URL = "https://example.com"
                result = await service.create_scheduled_meeting(host_id, payload)
            assert result == mock_meeting

    # --- list_meeting_invitations ---
    async def test_list_meeting_invitations_success(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        repo.list_invitations.return_value = [MagicMock(), MagicMock()]
        result = await service.list_meeting_invitations(meeting.id, meeting.host_id)
        assert len(result) == 2

    async def test_list_meeting_invitations_access_denied(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        bad_user = uuid.UUID("11111111-1111-1111-1111-111111111111")
        with pytest.raises(MeetingAccessDeniedException):
            await service.list_meeting_invitations(meeting.id, bad_user)

    # --- add_invitations ---
    async def test_add_invitations_success(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        repo.get_invitation_by_email.return_value = None
        new_invite = MagicMock(name="Invitee", email="invitee@example.com")
        repo.create_invitation.return_value = new_invite

        invites = [MagicMock(spec=InvitationCreate, name="Invitee", email="invitee@example.com")]
        with patch("app.modules.meetings.service.send_async_email") as mock_email:
            with patch("app.modules.meetings.service.settings") as mock_settings:
                mock_settings.FRONTEND_URL = "https://example.com"
                result = await service.add_invitations(meeting.host_id, meeting.id, invites)
            assert len(result) == 1
            mock_email.delay.assert_called_once()

    async def test_add_invitations_skip_existing(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        repo.get_invitation_by_email.return_value = MagicMock()

        invites = [MagicMock(spec=InvitationCreate, name="Existing", email="existing@example.com")]
        with patch("app.modules.meetings.service.send_async_email") as mock_email:
            result = await service.add_invitations(meeting.host_id, meeting.id, invites)
            assert len(result) == 0
            mock_email.delay.assert_not_called()

    async def test_add_invitations_email_failure(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        repo.get_invitation_by_email.return_value = None
        new_invite = MagicMock(name="Invitee", email="invitee@example.com")
        repo.create_invitation.return_value = new_invite

        invites = [MagicMock(spec=InvitationCreate, name="Invitee", email="invitee@example.com")]
        with patch("app.modules.meetings.service.send_async_email") as mock_email:
            mock_email.delay.side_effect = Exception("Email failed")
            with patch("app.modules.meetings.service.settings") as mock_settings:
                mock_settings.FRONTEND_URL = "https://example.com"
                result = await service.add_invitations(meeting.host_id, meeting.id, invites)
            assert len(result) == 1

    async def test_add_invitations_access_denied(self, service, repo):
        meeting = self._make_meeting()
        repo.get_by_id.return_value = meeting
        bad_user = uuid.UUID("11111111-1111-1111-1111-111111111111")
        with pytest.raises(MeetingAccessDeniedException):
            await service.add_invitations(bad_user, meeting.id, [])

    # --- _validate_participant_in_meeting ---
    async def test_validate_participant_in_meeting_none(self, service, repo):
        with pytest.raises(MeetingValidationError, match="not found"):
            await service._validate_participant_in_meeting(None, uuid.uuid4())

    async def test_validate_participant_in_meeting_session_mismatch(self, service, repo):
        participant = MagicMock(session_id=uuid.uuid4())
        session = MagicMock(meeting_id=uuid.uuid4())
        service.session_service.repo.get_by_id.return_value = session
        with pytest.raises(MeetingValidationError, match="context matching failed"):
            await service._validate_participant_in_meeting(participant, uuid.uuid4())

    async def test_validate_participant_in_meeting_success(self, service, repo):
        meeting_id = uuid.uuid4()
        participant = MagicMock(session_id=uuid.uuid4())
        session = MagicMock(meeting_id=meeting_id)
        service.session_service.repo.get_by_id.return_value = session
        result = await service._validate_participant_in_meeting(participant, meeting_id)
        assert result == session


class TestMeetingAIAnalysisService:
    @pytest.fixture
    def repo(self):
        mock = AsyncMock(spec=MeetingAIAnalysisRepository)
        mock.db = MagicMock()
        return mock

    @pytest.fixture
    def provider(self):
        return AsyncMock(spec=AIProviderService)

    @pytest.fixture
    def service(self, repo, provider):
        return MeetingAIAnalysisService(repo, provider)

    async def test_list_recent_analyses_for_user(self, service, repo):
        user_id = uuid.uuid4()
        repo.list_recent_for_user.return_value = [MagicMock()]
        result = await service.list_recent_analyses_for_user(user_id, limit=5)
        assert len(result) == 1
        repo.list_recent_for_user.assert_called_once_with(user_id, 5)

    async def test_get_analysis_success(self, service, repo):
        analysis = MagicMock(status=AIAnalysisStatus.COMPLETED)
        repo.get_by_session_id.return_value = analysis
        result = await service.get_analysis(uuid.uuid4())
        assert result == analysis

    async def test_get_analysis_not_found(self, service, repo):
        repo.get_by_session_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            await service.get_analysis(uuid.uuid4())
        assert exc.value.status_code == 404

    async def test_get_analysis_not_ready(self, service, repo):
        analysis = MagicMock(status=AIAnalysisStatus.PROCESSING)
        repo.get_by_session_id.return_value = analysis
        with pytest.raises(HTTPException) as exc:
            await service.get_analysis(uuid.uuid4())
        assert exc.value.status_code == 400

    async def test_get_analysis_status_success(self, service, repo):
        analysis = MagicMock()
        repo.get_by_session_id.return_value = analysis
        result = await service.get_analysis_status(uuid.uuid4())
        assert result == analysis

    async def test_get_analysis_status_not_found(self, service, repo):
        repo.get_by_session_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            await service.get_analysis_status(uuid.uuid4())
        assert exc.value.status_code == 404

    async def test_process_async_transcript_analysis_new_analysis(self, service, repo, provider):
        session_id = uuid.uuid4()
        repo.get_by_session_id.return_value = None
        analysis = MagicMock(id=uuid.uuid4())
        repo.create_analysis_placeholder.return_value = analysis

        provider.generate_transcript_analysis.return_value = {
            "parsed": {
                "summary": "Summary",
                "coverage_percentage": 85,
                "covered_points": ["point1"],
                "out_of_agenda_points": ["point2"],
                "suggested_tasks": [{"title": "Task1", "description": "Desc", "priority": "HIGH"}],
            },
            "raw": "raw response",
        }

        with patch("app.modules.ai_suggestions.repository.AISuggestionRepository") as mock_ai_suggestion_repo_cls:
            mock_ai_suggestion_repo = AsyncMock()
            mock_ai_suggestion_repo_cls.return_value = mock_ai_suggestion_repo
            await service.process_async_transcript_analysis(session_id, "Agenda", "Transcript")

        repo.update_status.assert_called()
        mock_ai_suggestion_repo.bulk_create.assert_called_once()

    async def test_process_async_transcript_analysis_existing_analysis(self, service, repo, provider):
        session_id = uuid.uuid4()
        analysis = MagicMock(id=uuid.uuid4())
        repo.get_by_session_id.return_value = analysis

        provider.generate_transcript_analysis.return_value = {
            "parsed": {
                "summary": "Summary",
                "coverage_percentage": 90,
                "covered_points": ["p1"],
                "out_of_agenda_points": ["p2"],
                "suggested_tasks": [],
            },
            "raw": "raw",
        }

        await service.process_async_transcript_analysis(session_id, "Agenda", "Transcript")
        repo.create_analysis_placeholder.assert_not_called()
        repo.update_status.assert_called()

    async def test_process_async_transcript_analysis_provider_error(self, service, repo, provider):
        session_id = uuid.uuid4()
        analysis = MagicMock(id=uuid.uuid4())
        repo.get_by_session_id.return_value = analysis
        provider.generate_transcript_analysis.side_effect = Exception("Provider error")

        with pytest.raises(Exception, match="Provider error"):
            await service.process_async_transcript_analysis(session_id, "Agenda", "Transcript")

        repo.update_status.assert_called_with(
            analysis.id,
            AIAnalysisStatus.FAILED,
            raw_response={"error_log_payload": "Provider error"},
        )


class TestMeetingSessionService:
    @pytest.fixture
    def repo(self):
        return AsyncMock(spec=MeetingSessionRepository)

    @pytest.fixture
    def redis(self):
        mock = AsyncMock()
        return mock

    @pytest.fixture
    def meeting_repo(self):
        return AsyncMock(spec=MeetingRepository)

    @pytest.fixture
    def service(self, repo, redis, meeting_repo):
        return MeetingSessionService(repo, redis, meeting_repo=meeting_repo)

    async def test_create_session(self, service, repo, redis):
        meeting_id = uuid.uuid4()
        host_id = uuid.uuid4()
        session = MagicMock(
            id=uuid.uuid4(), meeting_id=meeting_id,
            host_id=host_id, status=SessionStatus.ACTIVE,
            started_at=datetime.now(timezone.utc)
        )
        repo.create_session.return_value = session
        result = await service.create_session(meeting_id, host_id)
        assert result == session
        repo.create_session.assert_called_once_with(meeting_id, host_id)
        redis.hset.assert_called_once()

    async def test_finish_session_success(self, service, repo, redis):
        session_id = uuid.uuid4()
        session = MagicMock(id=session_id, meeting_id=uuid.uuid4())
        repo.finish_session.return_value = session
        result = await service.finish_session(session_id)
        assert result == session
        redis.delete.assert_called_once()

    async def test_finish_session_none(self, service, repo, redis):
        repo.finish_session.return_value = None
        result = await service.finish_session(uuid.uuid4())
        assert result is None
        redis.delete.assert_not_called()

    async def test_get_active_session_from_redis(self, service, repo, redis):
        meeting_id = uuid.uuid4()
        session_id = uuid.uuid4()
        redis.hgetall.return_value = {
            b"session_id": str(session_id).encode(),
            b"status": b"ACTIVE",
            b"host_id": str(uuid.uuid4()).encode(),
            b"started_at": b"2024-01-01T00:00:00+00:00",
        }
        session = MagicMock(id=session_id, status=SessionStatus.ACTIVE)
        repo.get_by_id.return_value = session
        result = await service.get_active_session(meeting_id)
        assert result == session

    async def test_get_active_session_redis_stale(self, service, repo, redis):
        meeting_id = uuid.uuid4()
        session_id = uuid.uuid4()
        redis.hgetall.return_value = {
            b"session_id": str(session_id).encode(),
            b"status": b"ACTIVE",
            b"host_id": str(uuid.uuid4()).encode(),
            b"started_at": b"2024-01-01T00:00:00+00:00",
        }
        inactive_session = MagicMock(id=session_id, status=SessionStatus.ENDED)
        repo.get_by_id.return_value = inactive_session
        repo.get_active_session.return_value = None
        result = await service.get_active_session(meeting_id)
        assert result is None
        redis.delete.assert_called_once_with(f"meeting:{meeting_id}")

    async def test_get_active_session_from_db(self, service, repo, redis):
        meeting_id = uuid.uuid4()
        redis.hgetall.return_value = {}
        session = MagicMock(status=SessionStatus.ACTIVE, id=uuid.uuid4())
        repo.get_active_session.return_value = session
        result = await service.get_active_session(meeting_id)
        assert result == session
        redis.hset.assert_called_once()

    async def test_get_active_session_no_session(self, service, repo, redis):
        meeting_id = uuid.uuid4()
        redis.hgetall.return_value = {}
        repo.get_active_session.return_value = None
        result = await service.get_active_session(meeting_id)
        assert result is None

    async def test_remove_live_state(self, service, repo, redis):
        meeting_id = uuid.uuid4()
        await service.remove_live_state(meeting_id)
        redis.delete.assert_called_once_with(f"meeting:{meeting_id}")

    async def test_list_sessions_for_user_as_host(self, service, repo, meeting_repo):
        meeting_id = uuid.uuid4()
        host_id = uuid.uuid4()
        user_id = host_id
        sessions = [MagicMock(id=uuid.uuid4()), MagicMock(id=uuid.uuid4())]
        repo.get_sessions_for_meeting.return_value = sessions
        repo.count_participants_for_session.return_value = 3
        result = await service.list_sessions_for_user(meeting_id, user_id, host_id)
        assert len(result) == 2
        assert result[0].participant_count == 3

    async def test_list_sessions_for_user_as_participant(self, service, repo, meeting_repo):
        meeting_id = uuid.uuid4()
        host_id = uuid.uuid4()
        user_id = uuid.uuid4()
        sessions = [MagicMock(id=uuid.uuid4())]
        meeting_repo.get_sessions_for_user.return_value = sessions
        repo.count_participants_for_session.return_value = 2
        result = await service.list_sessions_for_user(meeting_id, user_id, host_id)
        assert len(result) == 1
        meeting_repo.get_sessions_for_user.assert_called_once_with(meeting_id, user_id)

    async def test_get_session_detail_as_host(self, service, repo, meeting_repo):
        meeting_id = uuid.uuid4()
        session_id = uuid.uuid4()
        host_id = uuid.uuid4()
        session = MagicMock(id=session_id, meeting_id=meeting_id)
        repo.get_by_id.return_value = session
        repo.get_participants_for_session.return_value = [MagicMock(), MagicMock()]
        result = await service.get_session_detail(meeting_id, session_id, host_id, host_id)
        assert result == session
        assert len(result.participants) == 2

    async def test_get_session_detail_session_not_found(self, service, repo, meeting_repo):
        meeting_id = uuid.uuid4()
        session_id = uuid.uuid4()
        repo.get_by_id.return_value = None
        with pytest.raises(SessionAccessDeniedException):
            await service.get_session_detail(meeting_id, session_id, uuid.uuid4(), uuid.uuid4())

    async def test_get_session_detail_wrong_meeting(self, service, repo, meeting_repo):
        meeting_id = uuid.uuid4()
        session_id = uuid.uuid4()
        session = MagicMock(id=session_id, meeting_id=uuid.uuid4())
        repo.get_by_id.return_value = session
        with pytest.raises(SessionAccessDeniedException):
            await service.get_session_detail(meeting_id, session_id, uuid.uuid4(), uuid.uuid4())

    async def test_get_session_detail_non_host_no_participant(self, service, repo, meeting_repo):
        meeting_id = uuid.uuid4()
        session_id = uuid.uuid4()
        host_id = uuid.uuid4()
        user_id = uuid.uuid4()
        session = MagicMock(id=session_id, meeting_id=meeting_id)
        repo.get_by_id.return_value = session
        meeting_repo.get_last_participant.return_value = None
        with pytest.raises(SessionAccessDeniedException):
            await service.get_session_detail(meeting_id, session_id, user_id, host_id)

    async def test_get_session_detail_non_host_success(self, service, repo, meeting_repo):
        meeting_id = uuid.uuid4()
        session_id = uuid.uuid4()
        host_id = uuid.uuid4()
        user_id = uuid.uuid4()
        session = MagicMock(id=session_id, meeting_id=meeting_id)
        repo.get_by_id.return_value = session
        meeting_repo.get_last_participant.return_value = MagicMock()
        repo.get_participants_for_session.return_value = [MagicMock()]
        result = await service.get_session_detail(meeting_id, session_id, user_id, host_id)
        assert result == session