import uuid
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.main import app
from app.core.database import get_db
from app.core.redis import get_redis_client
from app.modules.calender.dependencies import (
    get_current_user_id,
    get_calendar_service,
    get_attachment_service,
)
from app.modules.calender.controller import CalendarController
from app.modules.calender.schema import (
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarEventResponse,
    CalendarOccurrenceResponse,
)
from app.modules.calender.service import CalendarService
from app.modules.attachments.service import AttachmentService
from app.modules.calender.enums import EventType, EventColor
from app.modules.calender.exceptions import (
    CalendarValidationError,
    EventNotFoundException,
    EventAccessDeniedException,
)
from app.modules.attachments.schemas import AttachmentListResponse, AttachmentResponse


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


class TestCalendarRoutes:
    async def test_create_event_success(self, client, override_deps):
        mock_service = MagicMock(spec=CalendarService)
        mock_event = MagicMock(spec=CalendarEventResponse)
        mock_event.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_event.title = "Meeting"
        mock_service.create_event.return_value = mock_event

        app.dependency_overrides[get_current_user_id] = lambda: _mock_current_user_id()
        app.dependency_overrides[get_calendar_service] = lambda: mock_service
        response = client.post(
            "/api/v1/calendar/events",
            json={
                "title": "Meeting",
                "start_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                "end_time": (datetime.now(timezone.utc) + timedelta(days=1, hours=1)).isoformat(),
            },
        )
        assert response.status_code == 201

    async def test_create_event_validation_error(self, client, override_deps):
        mock_service = MagicMock(spec=CalendarService)
        mock_service.create_event.side_effect = CalendarValidationError("Cannot create an event in the past.")
        app.dependency_overrides[get_current_user_id] = lambda: _mock_current_user_id()
        app.dependency_overrides[get_calendar_service] = lambda: mock_service
        response = client.post(
            "/api/v1/calendar/events",
            json={
                "title": "Meeting",
                "start_time": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 400

    async def test_get_analytics_success(self, client, override_deps):
        mock_service = MagicMock(spec=CalendarService)
        mock_service.get_analytics.return_value = {"total": 5, "today": 1}

        app.dependency_overrides[get_current_user_id] = lambda: _mock_current_user_id()
        app.dependency_overrides[get_calendar_service] = lambda: mock_service
        response = client.get("/api/v1/calendar/analytics")
        assert response.status_code == 200
        assert response.json()["total"] == 5

    async def test_get_event_success(self, client, override_deps):
        mock_service = MagicMock(spec=CalendarService)
        mock_event = MagicMock(spec=CalendarEventResponse)
        mock_event.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_service.get_event.return_value = mock_event

        event_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: _mock_current_user_id()
        app.dependency_overrides[get_calendar_service] = lambda: mock_service
        response = client.get(f"/api/v1/calendar/events/{event_id}")
        assert response.status_code == 200

    async def test_get_event_not_found(self, client, override_deps):
        mock_service = MagicMock(spec=CalendarService)
        mock_service.get_event.side_effect = EventNotFoundException(uuid.UUID("12345678-1234-5678-1234-567812345678"))

        event_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: _mock_current_user_id()
        app.dependency_overrides[get_calendar_service] = lambda: mock_service
        response = client.get(f"/api/v1/calendar/events/{event_id}")
        assert response.status_code == 404

    async def test_update_event_success(self, client, override_deps):
        mock_service = MagicMock(spec=CalendarService)
        mock_event = MagicMock(spec=CalendarEventResponse)
        mock_event.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_service.update_event.return_value = mock_event

        event_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: _mock_current_user_id()
        app.dependency_overrides[get_calendar_service] = lambda: mock_service
        response = client.patch(
            f"/api/v1/calendar/events/{event_id}",
            json={"title": "Updated Meeting"},
        )
        assert response.status_code == 200

    async def test_delete_event_success(self, client, override_deps):
        mock_service = MagicMock(spec=CalendarService)
        mock_service.delete_event.return_value = None

        event_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: _mock_current_user_id()
        app.dependency_overrides[get_calendar_service] = lambda: mock_service
        response = client.delete(f"/api/v1/calendar/events/{event_id}")
        assert response.status_code == 200
        assert "soft deleted" in response.json()["message"]

    async def test_list_events_success(self, client, override_deps):
        mock_service = MagicMock(spec=CalendarService)
        mock_occurrence = MagicMock(spec=CalendarOccurrenceResponse)
        mock_service.list_events.return_value = [mock_occurrence]

        app.dependency_overrides[get_current_user_id] = lambda: _mock_current_user_id()
        app.dependency_overrides[get_calendar_service] = lambda: mock_service
        response = client.get(
            "/api/v1/calendar/events",
            params={
                "start": datetime.now(timezone.utc).isoformat(),
                "end": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_list_events_with_filters(self, client, override_deps):
        mock_service = MagicMock(spec=CalendarService)
        mock_service.list_events.return_value = []

        app.dependency_overrides[get_current_user_id] = lambda: _mock_current_user_id()
        app.dependency_overrides[get_calendar_service] = lambda: mock_service
        response = client.get(
            "/api/v1/calendar/events",
            params={
                "start": datetime.now(timezone.utc).isoformat(),
                "end": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                "search": "meeting",
                "event_type": "MEETING",
                "color": "RED",
            },
        )
        assert response.status_code == 200

    async def test_upload_attachment_success(self, client, override_deps):
        mock_service = MagicMock(spec=CalendarService)
        mock_attachment_service = MagicMock(spec=AttachmentService)
        mock_attachment = MagicMock(spec=AttachmentResponse)
        mock_attachment_service.upload.return_value = mock_attachment

        event_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: _mock_current_user_id()
        app.dependency_overrides[get_calendar_service] = lambda: mock_service
        app.dependency_overrides[get_attachment_service] = lambda: mock_attachment_service
        response = client.post(
            f"/api/v1/calendar/events/{event_id}/attachments",
            files={"file": ("test.txt", b"hello", "text/plain")},
        )
        assert response.status_code == 201

    async def test_list_attachments_success(self, client, override_deps):
        mock_service = MagicMock(spec=CalendarService)
        mock_attachment_service = MagicMock(spec=AttachmentService)
        mock_attachment_service.list_all_for_entity.return_value = []
        mock_attachment_service.return_value = MagicMock()

        event_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: _mock_current_user_id()
        app.dependency_overrides[get_calendar_service] = lambda: mock_service
        app.dependency_overrides[get_attachment_service] = lambda: mock_attachment_service
        response = client.get(f"/api/v1/calendar/events/{event_id}/attachments")
        assert response.status_code == 200

    async def test_delete_attachment_success(self, client, override_deps):
        mock_service = MagicMock(spec=CalendarService)
        mock_attachment_service = MagicMock(spec=AttachmentService)

        event_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        attachment_id = str(uuid.UUID("87654321-4321-8765-4321-876543218765"))
        app.dependency_overrides[get_current_user_id] = lambda: _mock_current_user_id()
        app.dependency_overrides[get_calendar_service] = lambda: mock_service
        app.dependency_overrides[get_attachment_service] = lambda: mock_attachment_service
        response = client.delete(
            f"/api/v1/calendar/events/{event_id}/attachments/{attachment_id}"
        )
        assert response.status_code == 200
        assert "success" in response.json()["status"]

    async def test_unauthorized_without_token(self, client, override_deps):
        response = client.get("/api/v1/calendar/events")
        assert response.status_code == 401
