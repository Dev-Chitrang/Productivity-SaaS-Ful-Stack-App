import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status

from app.modules.meetings.controller import (
    MeetingController,
    MeetingAIAnalysisController,
    SessionHistoryController,
)
from app.modules.meetings.service import MeetingService, MeetingAIAnalysisService
from app.modules.meetings.exceptions import (
    MeetingNotFoundException,
    MeetingAccessDeniedException,
    MeetingValidationError,
    SessionAccessDeniedException,
)
from app.modules.meetings.enums import (
    MeetingStatus,
    ParticipantStatus,
    ParticipantType,
    AIAnalysisStatus,
)


class TestMeetingController:
    @pytest.fixture
    def mock_service(self):
        return AsyncMock(spec=MeetingService)

    @pytest.fixture
    def controller(self, mock_service):
        return MeetingController(mock_service)

    async def test_create_meeting(self, controller, mock_service):
        host_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        mock_meeting = MagicMock()
        mock_service.create_meeting.return_value = mock_meeting
        payload = MagicMock()
        with patch("app.modules.meetings.controller.MeetingResponse.model_validate", return_value={}):
            result = await controller.create_meeting(host_id, payload)
        mock_service.create_meeting.assert_called_once_with(host_id, payload)
        assert result == {}

    async def test_get_meeting_not_found(self, controller, mock_service):
        mock_service.get_meeting.side_effect = MeetingNotFoundException(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        with pytest.raises(HTTPException) as exc_info:
            await controller.get_meeting(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_meeting_access_denied(self, controller, mock_service):
        mock_service.update_meeting.side_effect = MeetingAccessDeniedException(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.UUID("87654321-4321-8765-4321-876543218765"))
        with pytest.raises(HTTPException) as exc_info:
            await controller.update_meeting(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"), MagicMock())
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_update_meeting_validation_error(self, controller, mock_service):
        mock_service.update_meeting.side_effect = MeetingValidationError("invalid")
        with pytest.raises(HTTPException) as exc_info:
            await controller.update_meeting(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"), MagicMock())
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_join_meeting_success(self, controller, mock_service):
        participant = MagicMock(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            session_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            user_id=None,
            guest_name="Guest",
            guest_email="guest@example.com",
            participant_type=ParticipantType.GUEST,
            status=ParticipantStatus.WAITING,
            is_muted=False,
            can_start_screen_share=False,
            joined_at=datetime.now(timezone.utc),
            left_at=None,
        )
        mock_service.join_meeting_flow.return_value = participant
        payload = MagicMock(guest_name="Guest", guest_email="guest@example.com")
        with patch("app.modules.meetings.controller.MeetingService.generate_meeting_session_token", return_value="token"):
            result = await controller.join_meeting(uuid.UUID("12345678-1234-5678-1234-567812345678"), None, payload)
        mock_service.join_meeting_flow.assert_called_once()
        assert result.guest_email == "guest@example.com"

    async def test_leave_meeting_validation_error(self, controller, mock_service):
        mock_service.leave_meeting.side_effect = MeetingValidationError("not active")
        with pytest.raises(HTTPException) as exc_info:
            await controller.leave_meeting(uuid.UUID("12345678-1234-5678-1234-567812345678"), user_id=uuid.uuid4())
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_upload_recording_session_access_denied(self, controller, mock_service):
        mock_service.save_recording_file.side_effect = SessionAccessDeniedException(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        file = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            await controller.upload_recording(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.UUID("87654321-4321-8765-4321-876543218765"), file, None)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_delete_recording_success(self, controller, mock_service):
        mock_service.remove_recording.return_value = None
        result = await controller.delete_recording(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.UUID("87654321-4321-8765-4321-876543218765"))
        assert result["status"] == "success"

    async def test_list_invites_access_denied(self, controller, mock_service):
        mock_service.list_meeting_invitations.side_effect = MeetingAccessDeniedException(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.UUID("87654321-4321-8765-4321-876543218765"))
        with pytest.raises(HTTPException) as exc_info:
            await controller.list_invites(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.UUID("87654321-4321-8765-4321-876543218765"))
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    # --- Additional controller method tests ---
    async def test_get_meeting_success(self, controller, mock_service):
        meeting = MagicMock()
        mock_service.get_meeting.return_value = meeting
        with patch("app.modules.meetings.controller.MeetingResponse.model_validate", return_value={"id": "123"}):
            result = await controller.get_meeting(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert result == {"id": "123"}

    async def test_update_meeting_success(self, controller, mock_service):
        meeting = MagicMock()
        mock_service.update_meeting.return_value = meeting
        with patch("app.modules.meetings.controller.MeetingResponse.model_validate", return_value={"updated": True}):
            result = await controller.update_meeting(
                uuid.UUID("87654321-4321-8765-4321-876543218765"),
                uuid.UUID("12345678-1234-5678-1234-567812345678"),
                MagicMock()
            )
        assert result == {"updated": True}

    async def test_update_meeting_not_found(self, controller, mock_service):
        mock_service.update_meeting.side_effect = MeetingNotFoundException(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        with pytest.raises(HTTPException) as exc_info:
            await controller.update_meeting(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"), MagicMock())
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_list_user_meetings(self, controller, mock_service):
        meetings = [MagicMock(), MagicMock()]
        mock_service.list_meetings.return_value = meetings
        with patch("app.modules.meetings.controller.MeetingResponse.model_validate", return_value={}):
            result = await controller.list_user_meetings(uuid.uuid4())
        assert len(result) == 2

    async def test_end_meeting_success(self, controller, mock_service):
        meeting = MagicMock()
        mock_service.end_meeting.return_value = meeting
        with patch("app.modules.meetings.controller.MeetingResponse.model_validate", return_value={"ended": True}):
            result = await controller.end_meeting(uuid.uuid4(), uuid.uuid4())
        assert result == {"ended": True}

    async def test_end_meeting_not_found(self, controller, mock_service):
        mock_service.end_meeting.side_effect = MeetingNotFoundException(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        with pytest.raises(HTTPException) as exc_info:
            await controller.end_meeting(uuid.uuid4(), uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_end_meeting_access_denied(self, controller, mock_service):
        mock_service.end_meeting.side_effect = MeetingAccessDeniedException(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await controller.end_meeting(uuid.uuid4(), uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_end_meeting_validation_error(self, controller, mock_service):
        mock_service.end_meeting.side_effect = MeetingValidationError("invalid")
        with pytest.raises(HTTPException) as exc_info:
            await controller.end_meeting(uuid.uuid4(), uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_cancel_meeting_success(self, controller, mock_service):
        meeting = MagicMock()
        mock_service.cancel_meeting.return_value = meeting
        with patch("app.modules.meetings.controller.MeetingResponse.model_validate", return_value={"cancelled": True}):
            result = await controller.cancel_meeting(uuid.uuid4(), uuid.uuid4())
        assert result == {"cancelled": True}

    async def test_cancel_meeting_not_found(self, controller, mock_service):
        mock_service.cancel_meeting.side_effect = MeetingNotFoundException(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        with pytest.raises(HTTPException) as exc_info:
            await controller.cancel_meeting(uuid.uuid4(), uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_cancel_meeting_access_denied(self, controller, mock_service):
        mock_service.cancel_meeting.side_effect = MeetingAccessDeniedException(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await controller.cancel_meeting(uuid.uuid4(), uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_cancel_meeting_validation_error(self, controller, mock_service):
        mock_service.cancel_meeting.side_effect = MeetingValidationError("invalid")
        with pytest.raises(HTTPException) as exc_info:
            await controller.cancel_meeting(uuid.uuid4(), uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_join_meeting_not_found(self, controller, mock_service):
        mock_service.join_meeting_flow.side_effect = MeetingNotFoundException(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        payload = MagicMock(guest_name="Guest", guest_email="guest@example.com")
        with pytest.raises(HTTPException) as exc_info:
            await controller.join_meeting(uuid.UUID("12345678-1234-5678-1234-567812345678"), None, payload)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_join_meeting_validation_error(self, controller, mock_service):
        mock_service.join_meeting_flow.side_effect = MeetingValidationError("invalid")
        payload = MagicMock(guest_name="Guest", guest_email="guest@example.com")
        with pytest.raises(HTTPException) as exc_info:
            await controller.join_meeting(uuid.UUID("12345678-1234-5678-1234-567812345678"), None, payload)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_get_meeting_by_code_success(self, controller, mock_service):
        meeting = MagicMock()
        mock_service.get_meeting_by_code.return_value = (meeting, "Host")
        with patch("app.modules.meetings.controller.MeetingJoinInfoResponse.model_validate") as mock_validate:
            mock_validate.return_value = MagicMock()
            mock_validate.return_value.model_dump.return_value = {"id": "123"}
            result = await controller.get_meeting_by_code("abc-defg-hij")
        assert "host_name" in result

    async def test_get_meeting_by_code_not_found(self, controller, mock_service):
        mock_service.get_meeting_by_code.side_effect = MeetingNotFoundException("not found")
        with pytest.raises(HTTPException) as exc_info:
            await controller.get_meeting_by_code("invalid")
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_participants_success(self, controller, mock_service):
        participants = [MagicMock(), MagicMock()]
        mock_service.list_participants.return_value = participants
        with patch("app.modules.meetings.controller.MeetingParticipantResponse.model_validate", return_value={}):
            result = await controller.get_participants(uuid.uuid4(), uuid.uuid4())
        assert len(result) == 2

    async def test_get_participants_not_found(self, controller, mock_service):
        mock_service.list_participants.side_effect = MeetingNotFoundException(uuid.uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await controller.get_participants(uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_participants_access_denied(self, controller, mock_service):
        mock_service.list_participants.side_effect = SessionAccessDeniedException(uuid.uuid4(), uuid.uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await controller.get_participants(uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_leave_meeting_success(self, controller, mock_service):
        participant = MagicMock()
        mock_service.leave_meeting.return_value = participant
        with patch("app.modules.meetings.controller.MeetingParticipantResponse.model_validate", return_value={"left": True}):
            result = await controller.leave_meeting(uuid.UUID("12345678-1234-5678-1234-567812345678"), user_id=uuid.uuid4())
        assert result == {"left": True}

    async def test_get_waiting_count_success(self, controller, mock_service):
        mock_service.get_waiting_count.return_value = 3
        result = await controller.get_waiting_count(uuid.uuid4())
        assert         result.waiting_count == 3

    async def test_get_waiting_count_not_found(self, controller, mock_service):
        mock_service.get_waiting_count.side_effect = MeetingNotFoundException(uuid.uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await controller.get_waiting_count(uuid.uuid4())
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_upload_recording_success(self, controller, mock_service):
        artifact = MagicMock()
        mock_service.save_recording_file.return_value = artifact
        with patch("app.modules.meetings.controller.RecordingResponse.model_validate", return_value={"uploaded": True}):
            result = await controller.upload_recording(uuid.uuid4(), uuid.uuid4(), MagicMock(), 120.0)
        assert result == {"uploaded": True}

    async def test_upload_recording_not_found(self, controller, mock_service):
        mock_service.save_recording_file.side_effect = MeetingNotFoundException(uuid.uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await controller.upload_recording(uuid.uuid4(), uuid.uuid4(), MagicMock(), None)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_upload_recording_validation_error(self, controller, mock_service):
        mock_service.save_recording_file.side_effect = MeetingValidationError("invalid")
        with pytest.raises(HTTPException) as exc_info:
            await controller.upload_recording(uuid.uuid4(), uuid.uuid4(), MagicMock(), None)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_upload_recording_attachment_error(self, controller, mock_service):
        from app.modules.attachments.exceptions import AttachmentValidationError
        mock_service.save_recording_file.side_effect = AttachmentValidationError("invalid")
        with pytest.raises(HTTPException) as exc_info:
            await controller.upload_recording(uuid.uuid4(), uuid.uuid4(), MagicMock(), None)
        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_upload_transcript_success(self, controller, mock_service):
        artifact = MagicMock()
        mock_service.save_transcript_file.return_value = artifact
        with patch("app.modules.meetings.controller.TranscriptResponse.model_validate", return_value={"uploaded": True}):
            result = await controller.upload_transcript(uuid.uuid4(), uuid.uuid4(), MagicMock())
        assert result == {"uploaded": True}

    async def test_upload_transcript_not_found(self, controller, mock_service):
        mock_service.save_transcript_file.side_effect = MeetingNotFoundException(uuid.uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await controller.upload_transcript(uuid.uuid4(), uuid.uuid4(), MagicMock())
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_upload_transcript_access_denied(self, controller, mock_service):
        mock_service.save_transcript_file.side_effect = SessionAccessDeniedException(uuid.uuid4(), uuid.uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await controller.upload_transcript(uuid.uuid4(), uuid.uuid4(), MagicMock())
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_upload_transcript_validation_error(self, controller, mock_service):
        mock_service.save_transcript_file.side_effect = MeetingValidationError("invalid")
        with pytest.raises(HTTPException) as exc_info:
            await controller.upload_transcript(uuid.uuid4(), uuid.uuid4(), MagicMock())
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_upload_transcript_attachment_error(self, controller, mock_service):
        from app.modules.attachments.exceptions import AttachmentValidationError
        mock_service.save_transcript_file.side_effect = AttachmentValidationError("invalid")
        with pytest.raises(HTTPException) as exc_info:
            await controller.upload_transcript(uuid.uuid4(), uuid.uuid4(), MagicMock())
        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_get_all_recordings(self, controller, mock_service):
        mock_service.list_recordings.return_value = [MagicMock(), MagicMock()]
        with patch("app.modules.meetings.controller.RecordingResponse.model_validate", return_value={}):
            result = await controller.get_all_recordings(uuid.uuid4(), uuid.uuid4())
        assert len(result) == 2

    async def test_get_all_transcripts(self, controller, mock_service):
        mock_service.list_transcripts.return_value = [MagicMock()]
        with patch("app.modules.meetings.controller.TranscriptResponse.model_validate", return_value={}):
            result = await controller.get_all_transcripts(uuid.uuid4(), uuid.uuid4())
        assert len(result) == 1

    async def test_download_recording_file_success(self, controller, mock_service):
        artifact = MagicMock(storage_path="/tmp/rec.webm", content_type="audio/webm", filename="rec.webm")
        mock_service.get_recording_artifact.return_value = artifact
        with patch("app.modules.meetings.controller.FileResponse") as mock_fr:
            mock_fr.return_value = MagicMock()
            result = await controller.download_recording_file(uuid.uuid4(), uuid.uuid4())
        mock_fr.assert_called_once_with(path="/tmp/rec.webm", media_type="audio/webm", filename="rec.webm")

    async def test_download_recording_file_not_found(self, controller, mock_service):
        mock_service.get_recording_artifact.side_effect = MeetingNotFoundException(uuid.uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await controller.download_recording_file(uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_download_recording_file_access_denied(self, controller, mock_service):
        mock_service.get_recording_artifact.side_effect = SessionAccessDeniedException(uuid.uuid4(), uuid.uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await controller.download_recording_file(uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_download_transcript_file_success(self, controller, mock_service):
        artifact = MagicMock(storage_path="/tmp/tx.txt", filename="tx.txt")
        mock_service.get_transcript_artifact.return_value = artifact
        with patch("app.modules.meetings.controller.FileResponse") as mock_fr:
            result = await controller.download_transcript_file(uuid.uuid4(), uuid.uuid4())
        mock_fr.assert_called_once_with(path="/tmp/tx.txt", media_type="text/plain", filename="tx.txt")

    async def test_download_transcript_file_not_found(self, controller, mock_service):
        mock_service.get_transcript_artifact.side_effect = MeetingNotFoundException(uuid.uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await controller.download_transcript_file(uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_download_transcript_file_access_denied(self, controller, mock_service):
        mock_service.get_transcript_artifact.side_effect = SessionAccessDeniedException(uuid.uuid4(), uuid.uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await controller.download_transcript_file(uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_delete_meeting_success(self, controller, mock_service):
        meeting = MagicMock()
        mock_service.delete_meeting.return_value = meeting
        with patch("app.modules.meetings.controller.MeetingResponse.model_validate", return_value={"deleted": True}):
            result = await controller.delete_meeting(uuid.uuid4(), uuid.uuid4())
        assert result == {"deleted": True}

    async def test_delete_meeting_not_found(self, controller, mock_service):
        mock_service.delete_meeting.side_effect = MeetingNotFoundException(uuid.uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await controller.delete_meeting(uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_meeting_access_denied(self, controller, mock_service):
        mock_service.delete_meeting.side_effect = MeetingAccessDeniedException(uuid.uuid4(), uuid.uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await controller.delete_meeting(uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_create_scheduled(self, controller, mock_service):
        meeting = MagicMock()
        mock_service.create_scheduled_meeting.return_value = meeting
        with patch("app.modules.meetings.controller.MeetingResponse.model_validate", return_value={"scheduled": True}):
            result = await controller.create_scheduled(uuid.uuid4(), MagicMock())
        assert result == {"scheduled": True}

    async def test_invite_participants(self, controller, mock_service):
        invites = [MagicMock(), MagicMock()]
        mock_service.add_invitations.return_value = invites
        with patch("app.modules.meetings.controller.InvitationResponse.model_validate", return_value={}):
            result = await controller.invite_participants(uuid.uuid4(), uuid.uuid4(), [MagicMock()])
        assert len(result) == 2

    async def test_list_invites_success(self, controller, mock_service):
        invitations = [MagicMock()]
        mock_service.list_meeting_invitations.return_value = invitations
        with patch("app.modules.meetings.controller.InvitationResponse.model_validate", return_value={}):
            result = await controller.list_invites(uuid.uuid4(), uuid.uuid4())
        assert len(result) == 1

    async def test_list_invites_not_found(self, controller, mock_service):
        mock_service.list_meeting_invitations.side_effect = MeetingNotFoundException(uuid.uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await controller.list_invites(uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_recording_not_found(self, controller, mock_service):
        mock_service.remove_recording.side_effect = MeetingNotFoundException(uuid.uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await controller.delete_recording(uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_recording_access_denied(self, controller, mock_service):
        mock_service.remove_recording.side_effect = MeetingAccessDeniedException(uuid.uuid4(), uuid.uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await controller.delete_recording(uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_delete_transcript_success(self, controller, mock_service):
        mock_service.remove_transcript.return_value = None
        result = await controller.delete_transcript(uuid.uuid4(), uuid.uuid4())
        assert result["status"] == "success"

    async def test_delete_transcript_not_found(self, controller, mock_service):
        mock_service.remove_transcript.side_effect = MeetingNotFoundException(uuid.uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await controller.delete_transcript(uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_transcript_access_denied(self, controller, mock_service):
        mock_service.remove_transcript.side_effect = MeetingAccessDeniedException(uuid.uuid4(), uuid.uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await controller.delete_transcript(uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestMeetingAIAnalysisController:
    @pytest.fixture
    def mock_service(self):
        return AsyncMock(spec=MeetingAIAnalysisService)

    @pytest.fixture
    def controller(self, mock_service):
        return MeetingAIAnalysisController(mock_service)

    async def test_get_completed_analysis_success(self, controller, mock_service):
        mock_analysis = MagicMock()
        mock_service.get_analysis.return_value = mock_analysis
        with patch("app.modules.meetings.controller.AIAnalysisResponse.model_validate", return_value={}):
            result = await controller.get_completed_analysis(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        mock_service.get_analysis.assert_called_once()
        assert result == {}

    async def test_list_recent_analyses(self, controller, mock_service):
        mock_service.list_recent_analyses_for_user.return_value = [
            (uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.uuid4(), AIAnalysisStatus.COMPLETED, "Summary", 85, datetime.now(timezone.utc), datetime.now(timezone.utc), uuid.uuid4(), "Meeting", datetime.now(timezone.utc))
        ]
        result = await controller.list_recent_analyses(uuid.UUID("87654321-4321-8765-4321-876543218765"), limit=5)
        assert len(result) == 1

    async def test_get_tracking_status(self, controller, mock_service):
        mock_analysis = MagicMock()
        mock_service.get_analysis_status.return_value = mock_analysis
        with patch("app.modules.meetings.controller.AIAnalysisStatusResponse.model_validate", return_value={}):
            result = await controller.get_tracking_status(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        mock_service.get_analysis_status.assert_called_once()
        assert result == {}


class TestSessionHistoryController:
    @pytest.fixture
    def mock_service(self):
        return AsyncMock(spec=MeetingService)

    @pytest.fixture
    def controller(self, mock_service):
        return SessionHistoryController(mock_service)

    async def test_list_success(self, controller, mock_service):
        meeting = MagicMock(host_id=uuid.UUID("87654321-4321-8765-4321-876543218765"))
        mock_service.get_meeting.return_value = meeting
        mock_session = MagicMock(
            id=uuid.uuid4(),
            meeting_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            status=MeetingStatus.ACTIVE,
            started_at=datetime.now(timezone.utc),
            participant_count=3,
        )
        mock_sessions = [mock_session]
        mock_service.session_service = AsyncMock()
        mock_service.session_service.list_sessions_for_user.return_value = mock_sessions
        with patch("app.modules.meetings.controller.SessionHistoryItemResponse", return_value=MagicMock()):
            result = await controller.list_sessions(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.UUID("87654321-4321-8765-4321-876543218765"))
        assert len(result) == 1

    async def test_list_meeting_not_found(self, controller, mock_service):
        mock_service.get_meeting.side_effect = MeetingNotFoundException(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        with pytest.raises(HTTPException) as exc_info:
            await controller.list_sessions(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.UUID("87654321-4321-8765-4321-876543218765"))
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_session_detail_success(self, controller, mock_service):
        meeting = MagicMock(host_id=uuid.uuid4())
        mock_service.get_meeting.return_value = meeting
        session = MagicMock(
            id=uuid.uuid4(), meeting_id=uuid.uuid4(),
            status=MeetingStatus.ACTIVE, started_at=datetime.now(timezone.utc),
            ended_at=None, duration_seconds=3600,
            participants=[]
        )
        mock_service.session_service = AsyncMock()
        mock_service.session_service.get_session_detail.return_value = session
        mock_service.repo = AsyncMock()
        mock_service.repo.list_recordings_by_session.return_value = []
        mock_service.repo.list_transcripts_by_session.return_value = []
        mock_service.repo.db = AsyncMock()
        with patch("app.modules.meetings.repository.MeetingAIAnalysisRepository") as mock_ai_repo_cls:
            mock_ai_repo = AsyncMock()
            mock_ai_repo.get_by_session_id.return_value = None
            mock_ai_repo_cls.return_value = mock_ai_repo
            result = await controller.get_session_detail(
                uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
            )
        assert result is not None