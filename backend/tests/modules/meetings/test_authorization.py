import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.meetings.repository import (
    MeetingRepository,
    MeetingAIAnalysisRepository,
    MeetingSessionRepository,
)
from app.modules.meetings.authorization import SessionAuthorizationService
from app.modules.meetings.enums import (
    MeetingStatus,
    ParticipantType,
    ParticipantStatus,
    MeetingType,
    SessionStatus,
)


class TestSessionAuthorizationService:
    @pytest.fixture
    def mock_meeting_repo(self):
        repo = AsyncMock(spec=MeetingRepository)
        return repo

    @pytest.fixture
    def mock_session_repo(self):
        repo = AsyncMock(spec=MeetingSessionRepository)
        return repo

    @pytest.fixture
    def auth_service(self, mock_meeting_repo, mock_session_repo):
        return SessionAuthorizationService(mock_meeting_repo, mock_session_repo)

    async def test_verify_session_access_raises_when_denied(self, auth_service):
        mock_meeting_repo = auth_service.repo
        mock_meeting_repo.get_by_id.return_value = None

        with pytest.raises(Exception):
            await auth_service.verify_session_access(
                uuid.UUID("12345678-1234-5678-1234-567812345678"),
                uuid.UUID("87654321-4321-8765-4321-876543218765"),
                uuid.UUID("11111111-1111-1111-1111-111111111111"),
            )

    async def test_can_access_session_returns_true_for_host(self, auth_service, mock_meeting_repo):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        mock_meeting = MagicMock()
        mock_meeting.host_id = user_id
        mock_meeting_repo.get_by_id.return_value = mock_meeting

        result = await auth_service.can_access_session(
            uuid.UUID("11111111-1111-1111-1111-111111111111"),
            user_id,
            meeting_id,
        )
        assert result is True

    async def test_can_access_session_returns_false_for_guest(self, auth_service, mock_meeting_repo):
        mock_meeting_repo.get_by_id.return_value = None

        result = await auth_service.can_access_session(
            uuid.UUID("11111111-1111-1111-1111-111111111111"),
            None,
            uuid.UUID("12345678-1234-5678-1234-567812345678"),
        )
        assert result is False

    async def test_get_accessible_session_ids_returns_all_for_host(
        self, auth_service, mock_meeting_repo, mock_session_repo
    ):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        mock_meeting = MagicMock()
        mock_meeting.host_id = user_id
        mock_meeting_repo.get_by_id.return_value = mock_meeting

        session1 = uuid.UUID("11111111-1111-1111-1111-111111111111")
        session2 = uuid.UUID("22222222-2222-2222-2222-222222222222")
        mock_session = MagicMock(id=session1)
        mock_session2 = MagicMock(id=session2)
        mock_session_repo.get_sessions_for_meeting.return_value = [mock_session, mock_session2]

        result = await auth_service.get_accessible_session_ids(user_id, meeting_id)
        assert result == {session1, session2}

    async def test_get_accessible_session_ids_returns_empty_for_guest(
        self, auth_service, mock_meeting_repo
    ):
        result = await auth_service.get_accessible_session_ids(
            None, uuid.UUID("12345678-1234-5678-1234-567812345678")
        )
        assert result == set()
