import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.main import app
from app.core.database import get_db
from app.core.redis import get_redis_client
from app.modules.meetings.dependencies import get_current_user_id, get_optional_user_id, get_meetings_service
from app.modules.meetings.repository import MeetingRepository, MeetingAIAnalysisRepository, MeetingSessionRepository
from app.modules.meetings.service import MeetingService, MeetingAIAnalysisService
from app.modules.meetings.controller import MeetingController, MeetingAIAnalysisController, SessionHistoryController
from app.modules.meetings.ai_provider_service import AIProviderService
from app.modules.meetings.enums import MeetingStatus, ParticipantStatus, ParticipantType
from app.modules.meetings.exceptions import MeetingNotFoundException


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_redis():
    mock = AsyncMock(spec=Redis)
    mock_pipeline = AsyncMock()
    mock_pipeline.zremrangebyscore = MagicMock()
    mock_pipeline.zcard = MagicMock()
    mock_pipeline.zrange = MagicMock()
    mock_pipeline.zadd = MagicMock()
    mock_pipeline.expire = MagicMock()
    mock_pipeline.execute = AsyncMock(return_value=[0, 0, []])
    mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
    mock_pipeline.__aexit__ = AsyncMock(return_value=False)
    mock.pipeline.return_value = mock_pipeline
    return mock


@pytest.fixture
def override_deps(mock_db, mock_redis):
    def _get_db():
        return mock_db

    def _get_redis():
        return mock_redis

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_redis_client] = _get_redis
    yield
    app.dependency_overrides.clear()


def _mock_current_user_id():
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


class TestMeetingRoutes:
    async def test_create_meeting_success(self, client, override_deps, mock_db, mock_redis):
        mock_service = MagicMock(spec=MeetingService)
        mock_meeting = MagicMock()
        mock_meeting.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_meeting.title = "New Meeting"
        mock_meeting.description = "Description"
        mock_meeting.agenda = None
        mock_meeting.host_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        mock_meeting.timezone = "UTC"
        mock_meeting.meeting_code = "abc-defg-hij"
        mock_meeting.meeting_link = "https://workspace.app/m/abc-defg-hij"
        mock_meeting.status = MeetingStatus.CREATED
        mock_meeting.meeting_type = "INSTANT"
        mock_meeting.created_at = datetime.now(timezone.utc)
        mock_meeting.updated_at = datetime.now(timezone.utc)
        mock_meeting.ended_at = None
        mock_meeting.deleted_at = None
        mock_meeting.invited_participants_count = 0
        mock_meeting.active_screen_sharer_id = None
        mock_service.create_meeting.return_value = mock_meeting

        app.dependency_overrides[get_meetings_service] = lambda: mock_service
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        response = client.post(
            "/api/v1/meetings/",
            json={"title": "New Meeting"},
            headers={"Authorization": "Bearer valid_token"},
        )
        assert response.status_code == 201

    async def test_list_meetings(self, client, override_deps, mock_db, mock_redis):
        mock_service = MagicMock(spec=MeetingService)
        mock_meeting = MagicMock()
        mock_meeting.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_meeting.title = "Meeting 1"
        mock_meeting.description = "Description"
        mock_meeting.agenda = None
        mock_meeting.host_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        mock_meeting.timezone = "UTC"
        mock_meeting.meeting_code = "abc-defg-hij"
        mock_meeting.meeting_link = "https://workspace.app/m/abc-defg-hij"
        mock_meeting.status = MeetingStatus.CREATED
        mock_meeting.meeting_type = "INSTANT"
        mock_meeting.created_at = datetime.now(timezone.utc)
        mock_meeting.updated_at = datetime.now(timezone.utc)
        mock_meeting.ended_at = None
        mock_meeting.deleted_at = None
        mock_meeting.invited_participants_count = 0
        mock_meeting.active_screen_sharer_id = None
        mock_service.list_meetings.return_value = [mock_meeting]

        app.dependency_overrides[get_meetings_service] = lambda: mock_service
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        response = client.get(
            "/api/v1/meetings",
            headers={"Authorization": "Bearer valid_token"},
        )
        assert response.status_code == 200

    async def test_join_meeting_success(self, client, override_deps, mock_db, mock_redis):
        mock_service = MagicMock(spec=MeetingService)
        participant = MagicMock()
        participant.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        participant.session_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        participant.user_id = None
        participant.guest_name = "Guest"
        participant.guest_email = "guest@example.com"
        participant.participant_type = ParticipantType.GUEST
        participant.status = ParticipantStatus.WAITING
        participant.is_muted = False
        participant.can_start_screen_share = False
        participant.joined_at = datetime.now(timezone.utc)
        participant.left_at = None
        mock_service.join_meeting_flow.return_value = participant

        app.dependency_overrides[get_meetings_service] = lambda: mock_service
        app.dependency_overrides[get_optional_user_id] = lambda: None
        with patch("app.modules.meetings.controller.MeetingService.generate_meeting_session_token", return_value="token"), \
             patch("app.modules.meetings.routes.ws_connection_manager.broadcast_to_room", new_callable=AsyncMock):
            response = client.post(
                "/api/v1/meetings/12345678-1234-5678-1234-567812345678/join",
                json={"guest_name": "Guest", "guest_email": "guest@example.com"},
            )
            assert response.status_code == 200

    async def test_get_meeting_by_code_not_found(self, client, override_deps, mock_db, mock_redis):
        mock_service = MagicMock(spec=MeetingService)
        mock_service.get_meeting_by_code.side_effect = MeetingNotFoundException("not found")

        app.dependency_overrides[get_meetings_service] = lambda: mock_service
        response = client.get("/api/v1/meetings/by-code/abc-defg-hij")
        assert response.status_code == 404


from app.modules.meetings.exceptions import (
    MeetingAccessDeniedException,
    MeetingValidationError,
    SessionAccessDeniedException,
)
from app.modules.meetings.schemas import MeetingParticipantResponse
from app.modules.meetings.enums import AIAnalysisStatus

# ── Shared IDs ────────────────────────────────────────────────────────────────
_MEETING_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")
_USER_ID = uuid.UUID("87654321-4321-8765-4321-876543218765")
_PARTICIPANT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_SESSION_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_RECORDING_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_TRANSCRIPT_ID = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")


def _meeting_stub(
    mid=_MEETING_ID,
    host_id=_USER_ID,
    status=MeetingStatus.ACTIVE,
):
    m = MagicMock()
    m.id = mid
    m.title = "Test Meeting"
    m.description = "Desc"
    m.agenda = None
    m.host_id = host_id
    m.timezone = "UTC"
    m.meeting_code = "abc-defg-hij"
    m.meeting_link = "https://workspace.app/m/abc-defg-hij"
    m.status = status
    m.meeting_type = "INSTANT"
    m.created_at = datetime.now(timezone.utc)
    m.updated_at = datetime.now(timezone.utc)
    m.ended_at = None
    m.deleted_at = None
    m.invited_participants_count = 0
    m.active_screen_sharer_id = None
    return m


def _participant_stub(pid=_PARTICIPANT_ID, status=ParticipantStatus.ADMITTED, uid=_USER_ID):
    p = MagicMock()
    p.id = pid
    p.session_id = _SESSION_ID
    p.user_id = uid
    p.guest_name = None
    p.guest_email = None
    p.participant_type = ParticipantType.REGISTERED
    p.status = status
    p.is_muted = False
    p.can_start_screen_share = False
    p.joined_at = datetime.now(timezone.utc)
    p.left_at = None
    return p


def _mock_svc():
    svc = MagicMock(spec=MeetingService)
    svc.session_service = MagicMock()
    svc.session_service.get_active_session = AsyncMock(return_value=None)
    svc.auth_service = MagicMock()
    svc.auth_service.verify_session_access = AsyncMock(return_value=None)
    svc.repo = MagicMock()
    svc.repo.list_recordings_by_session = AsyncMock(return_value=[])
    svc.repo.list_transcripts_by_session = AsyncMock(return_value=[])
    return svc


# ── End meeting ───────────────────────────────────────────────────────────────

class TestEndMeetingRoute:
    async def test_end_meeting_success_broadcasts(self, client, override_deps):
        svc = _mock_svc()
        meeting = _meeting_stub(status=MeetingStatus.ENDED)
        svc.end_meeting = AsyncMock(return_value=meeting)
        app.dependency_overrides[get_meetings_service] = lambda: svc
        app.dependency_overrides[get_current_user_id] = lambda: _USER_ID
        with patch("app.modules.meetings.routes.ws_connection_manager.broadcast_to_room", new_callable=AsyncMock) as mock_bc:
            response = client.post(f"/api/v1/meetings/{_MEETING_ID}/end")
        assert response.status_code == 200
        mock_bc.assert_called_once()
        assert mock_bc.call_args[0][1]["event"] == "meeting_ended"

    async def test_end_meeting_access_denied_returns_403(self, client, override_deps):
        svc = _mock_svc()
        svc.end_meeting = AsyncMock(side_effect=MeetingAccessDeniedException(_MEETING_ID, _USER_ID))
        app.dependency_overrides[get_meetings_service] = lambda: svc
        app.dependency_overrides[get_current_user_id] = lambda: _USER_ID
        with patch("app.modules.meetings.routes.ws_connection_manager.broadcast_to_room", new_callable=AsyncMock):
            response = client.post(f"/api/v1/meetings/{_MEETING_ID}/end")
        assert response.status_code == 403

    async def test_end_meeting_not_found_returns_404(self, client, override_deps):
        svc = _mock_svc()
        svc.end_meeting = AsyncMock(side_effect=MeetingNotFoundException(_MEETING_ID))
        app.dependency_overrides[get_meetings_service] = lambda: svc
        app.dependency_overrides[get_current_user_id] = lambda: _USER_ID
        with patch("app.modules.meetings.routes.ws_connection_manager.broadcast_to_room", new_callable=AsyncMock):
            response = client.post(f"/api/v1/meetings/{_MEETING_ID}/end")
        assert response.status_code == 404

    async def test_end_meeting_validation_error_returns_4xx(self, client, override_deps):
        svc = _mock_svc()
        svc.end_meeting = AsyncMock(side_effect=MeetingValidationError("Already ended"))
        app.dependency_overrides[get_meetings_service] = lambda: svc
        app.dependency_overrides[get_current_user_id] = lambda: _USER_ID
        with patch("app.modules.meetings.routes.ws_connection_manager.broadcast_to_room", new_callable=AsyncMock):
            response = client.post(f"/api/v1/meetings/{_MEETING_ID}/end")
        assert response.status_code in (400, 422)


# ── Leave meeting ─────────────────────────────────────────────────────────────

class TestLeaveMeetingRoute:
    def _left_participant(self):
        return MeetingParticipantResponse(
            id=_PARTICIPANT_ID,
            session_id=_SESSION_ID,
            user_id=_USER_ID,
            user_name=None,
            guest_name=None,
            guest_email=None,
            participant_type=ParticipantType.REGISTERED,
            status=ParticipantStatus.LEFT,
            is_muted=False,
            can_start_screen_share=False,
            joined_at=datetime.now(timezone.utc),
            left_at=None,
        )

    async def test_leave_as_authenticated_user(self, client, override_deps):
        svc = _mock_svc()
        svc.leave_meeting = AsyncMock(return_value=self._left_participant())
        app.dependency_overrides[get_meetings_service] = lambda: svc
        app.dependency_overrides[get_optional_user_id] = lambda: _USER_ID
        response = client.post(f"/api/v1/meetings/{_MEETING_ID}/leave", json={})
        assert response.status_code == 200

    async def test_leave_as_guest_with_email(self, client, override_deps):
        svc = _mock_svc()
        svc.leave_meeting = AsyncMock(return_value=self._left_participant())
        app.dependency_overrides[get_meetings_service] = lambda: svc
        app.dependency_overrides[get_optional_user_id] = lambda: None
        response = client.post(
            f"/api/v1/meetings/{_MEETING_ID}/leave",
            json={"guest_email": "guest@example.com"},
        )
        assert response.status_code == 200

    async def test_leave_no_auth_no_email_returns_401(self, client, override_deps):
        svc = _mock_svc()
        app.dependency_overrides[get_meetings_service] = lambda: svc
        app.dependency_overrides[get_optional_user_id] = lambda: None
        response = client.post(f"/api/v1/meetings/{_MEETING_ID}/leave", json={})
        assert response.status_code == 401


# ── Participant actions ────────────────────────────────────────────────────────

class TestParticipantActions:
    async def test_admit_participant_broadcasts_and_returns_admitted(self, client, override_deps):
        svc = _mock_svc()
        p = _participant_stub(status=ParticipantStatus.ADMITTED)
        svc.update_participant_status = AsyncMock(return_value=p)
        app.dependency_overrides[get_meetings_service] = lambda: svc
        app.dependency_overrides[get_current_user_id] = lambda: _USER_ID
        with patch("app.modules.meetings.routes.ws_connection_manager.broadcast_to_room", new_callable=AsyncMock) as bc:
            response = client.post(f"/api/v1/meetings/{_MEETING_ID}/participants/{_PARTICIPANT_ID}/admit")
        assert response.status_code == 200
        assert response.json()["status"] == "admitted"
        bc.assert_called_once()

    async def test_reject_participant_notifies_via_ws_if_connected(self, client, override_deps):
        svc = _mock_svc()
        p = _participant_stub(status=ParticipantStatus.REJECTED)
        svc.update_participant_status = AsyncMock(return_value=p)
        app.dependency_overrides[get_meetings_service] = lambda: svc
        app.dependency_overrides[get_current_user_id] = lambda: _USER_ID
        mock_ws = MagicMock()
        mock_ws.send_text = AsyncMock()
        with patch(
            "app.modules.meetings.routes.ws_connection_manager.active_rooms",
            {str(_MEETING_ID): {str(_PARTICIPANT_ID): mock_ws}},
        ), patch(
            "app.modules.meetings.routes.ws_connection_manager.send_personal_message",
            new_callable=AsyncMock,
        ) as spm:
            response = client.post(f"/api/v1/meetings/{_MEETING_ID}/participants/{_PARTICIPANT_ID}/reject")
        assert response.status_code == 200
        assert response.json()["status"] == "rejected"
        spm.assert_called_once()

    async def test_reject_participant_no_ws_connection_still_returns_ok(self, client, override_deps):
        svc = _mock_svc()
        p = _participant_stub(status=ParticipantStatus.REJECTED)
        svc.update_participant_status = AsyncMock(return_value=p)
        app.dependency_overrides[get_meetings_service] = lambda: svc
        app.dependency_overrides[get_current_user_id] = lambda: _USER_ID
        with patch("app.modules.meetings.routes.ws_connection_manager.active_rooms", {}):
            response = client.post(f"/api/v1/meetings/{_MEETING_ID}/participants/{_PARTICIPANT_ID}/reject")
        assert response.status_code == 200

    async def test_remove_participant_broadcasts_left(self, client, override_deps):
        svc = _mock_svc()
        p = _participant_stub(status=ParticipantStatus.REMOVED)
        svc.update_participant_status = AsyncMock(return_value=p)
        app.dependency_overrides[get_meetings_service] = lambda: svc
        app.dependency_overrides[get_current_user_id] = lambda: _USER_ID
        with patch("app.modules.meetings.routes.ws_connection_manager.active_rooms", {}), \
             patch("app.modules.meetings.routes.ws_connection_manager.broadcast_to_room", new_callable=AsyncMock) as bc:
            response = client.post(f"/api/v1/meetings/{_MEETING_ID}/participants/{_PARTICIPANT_ID}/remove")
        assert response.status_code == 200
        broadcast_events = [c[0][1]["event"] for c in bc.call_args_list]
        assert "participant_left" in broadcast_events

    async def test_mute_participant_broadcasts_mute_changed(self, client, override_deps):
        svc = _mock_svc()
        p = _participant_stub()
        p.is_muted = True
        svc.toggle_participant_mute = AsyncMock(return_value=p)
        app.dependency_overrides[get_meetings_service] = lambda: svc
        app.dependency_overrides[get_current_user_id] = lambda: _USER_ID
        with patch("app.modules.meetings.routes.ws_connection_manager.broadcast_to_room", new_callable=AsyncMock) as bc:
            response = client.post(f"/api/v1/meetings/{_MEETING_ID}/participants/{_PARTICIPANT_ID}/mute")
        assert response.status_code == 200
        assert response.json()["status"] == "muted"
        payload = bc.call_args[0][1]
        assert payload["event"] == "mute_changed"
        assert payload["data"]["is_muted"] is True

    async def test_unmute_participant_broadcasts_mute_changed(self, client, override_deps):
        svc = _mock_svc()
        p = _participant_stub()
        p.is_muted = False
        svc.toggle_participant_mute = AsyncMock(return_value=p)
        app.dependency_overrides[get_meetings_service] = lambda: svc
        app.dependency_overrides[get_current_user_id] = lambda: _USER_ID
        with patch("app.modules.meetings.routes.ws_connection_manager.broadcast_to_room", new_callable=AsyncMock) as bc:
            response = client.post(f"/api/v1/meetings/{_MEETING_ID}/participants/{_PARTICIPANT_ID}/unmute")
        assert response.status_code == 200
        assert response.json()["status"] == "unmuted"
        assert bc.call_args[0][1]["data"]["is_muted"] is False


# ── Session history ────────────────────────────────────────────────────────────

class TestSessionHistoryRoutes:
    async def test_list_sessions_delegates_to_ctrl(self, client, override_deps):
        svc = _mock_svc()
        session_item = MagicMock()
        session_item.id = _SESSION_ID
        session_item.meeting_id = _MEETING_ID
        session_item.started_at = datetime.now(timezone.utc)
        session_item.ended_at = None
        session_item.status = "ENDED"
        session_item.has_recording = False
        session_item.has_transcript = False
        session_item.has_ai_analysis = False
        svc.list_sessions = AsyncMock(return_value=[session_item])
        app.dependency_overrides[get_meetings_service] = lambda: svc
        app.dependency_overrides[get_current_user_id] = lambda: _USER_ID
        with patch("app.modules.meetings.controller.SessionHistoryController.list_sessions", new_callable=AsyncMock, return_value=[session_item]):
            response = client.get(f"/api/v1/meetings/{_MEETING_ID}/sessions")
        assert response.status_code == 200

    async def test_session_recordings_access_denied_returns_403(self, client, override_deps):
        svc = _mock_svc()
        svc.get_meeting = AsyncMock(return_value=_meeting_stub())
        svc.auth_service.verify_session_access = AsyncMock(
            side_effect=SessionAccessDeniedException(_SESSION_ID, _USER_ID)
        )
        app.dependency_overrides[get_meetings_service] = lambda: svc
        app.dependency_overrides[get_current_user_id] = lambda: _USER_ID
        response = client.get(f"/api/v1/meetings/{_MEETING_ID}/sessions/{_SESSION_ID}/recordings")
        assert response.status_code == 403

    async def test_session_recordings_meeting_not_found_returns_404(self, client, override_deps):
        svc = _mock_svc()
        svc.get_meeting = AsyncMock(side_effect=MeetingNotFoundException(_MEETING_ID))
        app.dependency_overrides[get_meetings_service] = lambda: svc
        app.dependency_overrides[get_current_user_id] = lambda: _USER_ID
        response = client.get(f"/api/v1/meetings/{_MEETING_ID}/sessions/{_SESSION_ID}/recordings")
        assert response.status_code == 404

    async def test_session_transcripts_access_denied_returns_403(self, client, override_deps):
        svc = _mock_svc()
        svc.get_meeting = AsyncMock(return_value=_meeting_stub())
        svc.auth_service.verify_session_access = AsyncMock(
            side_effect=SessionAccessDeniedException(_SESSION_ID, _USER_ID)
        )
        app.dependency_overrides[get_meetings_service] = lambda: svc
        app.dependency_overrides[get_current_user_id] = lambda: _USER_ID
        response = client.get(f"/api/v1/meetings/{_MEETING_ID}/sessions/{_SESSION_ID}/transcripts")
        assert response.status_code == 403

    async def test_session_analysis_access_denied_returns_403(self, client, override_deps):
        from app.modules.meetings.routes import get_ai_analysis_service
        svc = _mock_svc()
        svc.get_meeting = AsyncMock(return_value=_meeting_stub())
        svc.auth_service.verify_session_access = AsyncMock(
            side_effect=SessionAccessDeniedException(_SESSION_ID, _USER_ID)
        )
        ai_svc = MagicMock(spec=MeetingAIAnalysisService)
        app.dependency_overrides[get_meetings_service] = lambda: svc
        app.dependency_overrides[get_current_user_id] = lambda: _USER_ID
        app.dependency_overrides[get_ai_analysis_service] = lambda: ai_svc
        response = client.get(f"/api/v1/meetings/{_MEETING_ID}/sessions/{_SESSION_ID}/analysis")
        assert response.status_code == 403


# ── AI analysis endpoints ──────────────────────────────────────────────────────

class TestAIAnalysisRoutes:
    async def test_analysis_no_active_session_returns_404(self, client, override_deps):
        from app.modules.meetings.routes import get_ai_analysis_service
        svc = _mock_svc()
        svc.session_service.get_active_session = AsyncMock(return_value=None)
        ai_svc = MagicMock(spec=MeetingAIAnalysisService)
        app.dependency_overrides[get_meetings_service] = lambda: svc
        app.dependency_overrides[get_current_user_id] = lambda: _USER_ID
        app.dependency_overrides[get_ai_analysis_service] = lambda: ai_svc
        response = client.get(f"/api/v1/meetings/{_MEETING_ID}/analysis")
        assert response.status_code == 404

    async def test_analysis_status_no_active_session_returns_404(self, client, override_deps):
        from app.modules.meetings.routes import get_ai_analysis_service
        svc = _mock_svc()
        svc.session_service.get_active_session = AsyncMock(return_value=None)
        ai_svc = MagicMock(spec=MeetingAIAnalysisService)
        app.dependency_overrides[get_meetings_service] = lambda: svc
        app.dependency_overrides[get_current_user_id] = lambda: _USER_ID
        app.dependency_overrides[get_ai_analysis_service] = lambda: ai_svc
        response = client.get(f"/api/v1/meetings/{_MEETING_ID}/analysis/status")
        assert response.status_code == 404

    async def test_analysis_session_access_denied_returns_403(self, client, override_deps):
        from app.modules.meetings.routes import get_ai_analysis_service
        svc = _mock_svc()
        mock_session = MagicMock()
        mock_session.id = _SESSION_ID
        svc.session_service.get_active_session = AsyncMock(return_value=mock_session)
        svc.auth_service.verify_session_access = AsyncMock(
            side_effect=SessionAccessDeniedException(_SESSION_ID, _USER_ID)
        )
        ai_svc = MagicMock(spec=MeetingAIAnalysisService)
        app.dependency_overrides[get_meetings_service] = lambda: svc
        app.dependency_overrides[get_current_user_id] = lambda: _USER_ID
        app.dependency_overrides[get_ai_analysis_service] = lambda: ai_svc
        response = client.get(f"/api/v1/meetings/{_MEETING_ID}/analysis")
        assert response.status_code == 403


# ── Screen share ───────────────────────────────────────────────────────────────

class TestScreenShareRoutes:
    async def test_request_screen_share_not_found_returns_404(self, client, override_deps):
        svc = _mock_svc()
        svc.request_screen_share = AsyncMock(side_effect=MeetingNotFoundException(_MEETING_ID))
        app.dependency_overrides[get_meetings_service] = lambda: svc
        response = client.post(
            f"/api/v1/meetings/{_MEETING_ID}/screen-share/request",
            json={"participant_id": str(_PARTICIPANT_ID)},
        )
        assert response.status_code == 404

    async def test_request_screen_share_already_sharing_returns_409(self, client, override_deps):
        svc = _mock_svc()
        svc.request_screen_share = AsyncMock(
            side_effect=MeetingValidationError("already sharing")
        )
        app.dependency_overrides[get_meetings_service] = lambda: svc
        response = client.post(
            f"/api/v1/meetings/{_MEETING_ID}/screen-share/request",
            json={"participant_id": str(_PARTICIPANT_ID)},
        )
        assert response.status_code == 409

    async def test_request_screen_share_other_validation_returns_400(self, client, override_deps):
        svc = _mock_svc()
        svc.request_screen_share = AsyncMock(
            side_effect=MeetingValidationError("meeting not active")
        )
        app.dependency_overrides[get_meetings_service] = lambda: svc
        response = client.post(
            f"/api/v1/meetings/{_MEETING_ID}/screen-share/request",
            json={"participant_id": str(_PARTICIPANT_ID)},
        )
        assert response.status_code == 400

    async def test_request_screen_share_success_broadcasts(self, client, override_deps):
        svc = _mock_svc()
        p = _participant_stub()
        svc.request_screen_share = AsyncMock(return_value=p)
        app.dependency_overrides[get_meetings_service] = lambda: svc
        with patch("app.modules.meetings.routes.ws_connection_manager.broadcast_to_room", new_callable=AsyncMock) as bc:
            response = client.post(
                f"/api/v1/meetings/{_MEETING_ID}/screen-share/request",
                json={"participant_id": str(_PARTICIPANT_ID)},
            )
        assert response.status_code == 200
        bc.assert_called_once()
        assert bc.call_args[0][1]["event"] == "screen_share_requested"
