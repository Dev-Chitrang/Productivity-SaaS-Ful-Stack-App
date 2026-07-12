import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException, status
from app.modules.calender.service import CalendarService
from app.modules.calender.controller import CalendarController
from app.modules.calender.schema import (
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarEventResponse,
    CalendarOccurrenceResponse,
)
from app.modules.calender.enums import EventType, EventColor, RecurrenceFrequency
from app.modules.calender.exceptions import (
    EventNotFoundException,
    EventAccessDeniedException,
    CalendarValidationError,
)


class TestCalendarController:
    @pytest.fixture
    def controller(self):
        service = MagicMock(spec=CalendarService)
        return CalendarController(service)

    def _make_event_response(self, **kwargs):
        now = datetime.now(timezone.utc)
        return CalendarEventResponse(
            id=kwargs.get("id", uuid.UUID("12345678-1234-5678-1234-567812345678")),
            user_id=kwargs.get("user_id", uuid.UUID("87654321-4321-8765-4321-876543218765")),
            title=kwargs.get("title", "Test Event"),
            description=kwargs.get("description", "Desc"),
            event_type=kwargs.get("event_type", EventType.MEETING),
            color=kwargs.get("color", EventColor.BLUE),
            start_time=kwargs.get("start_time", now + timedelta(days=1)),
            end_time=kwargs.get("end_time", now + timedelta(days=1, hours=1)),
            timezone=kwargs.get("timezone", "UTC"),
            is_all_day=kwargs.get("is_all_day", False),
            location=kwargs.get("location", None),
            created_at=now,
            updated_at=now,
        )

    async def test_create_user_event_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        mock_event = self._make_event_response()
        controller.service.create_event.return_value = mock_event

        payload = CalendarEventCreate(
            title="New Meeting",
            start_time=datetime.now(timezone.utc) + timedelta(days=1),
            end_time=datetime.now(timezone.utc) + timedelta(days=1, hours=1),
        )
        result = await controller.create_user_event(user_id, payload)
        assert result.title == "Test Event"

    async def test_create_user_event_validation_error(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        controller.service.create_event.side_effect = CalendarValidationError("bad input")
        payload = CalendarEventCreate(
            title="Bad",
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc),
        )
        with pytest.raises(HTTPException) as exc_info:
            await controller.create_user_event(user_id, payload)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_get_user_event_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        event_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_event = self._make_event_response()
        controller.service.get_event.return_value = mock_event

        result = await controller.get_user_event(user_id, event_id)
        assert result.id == event_id

    async def test_get_user_event_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        event_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.get_event.side_effect = EventNotFoundException(event_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.get_user_event(user_id, event_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_user_event_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        event_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.get_event.side_effect = EventAccessDeniedException(
            event_id, user_id
        )
        with pytest.raises(HTTPException) as exc_info:
            await controller.get_user_event(user_id, event_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_update_user_event_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        event_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_event = self._make_event_response(title="Updated")
        controller.service.update_event.return_value = mock_event

        payload = CalendarEventUpdate(title="Updated")
        result = await controller.update_user_event(user_id, event_id, payload)
        assert result.title == "Updated"

    async def test_update_user_event_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        event_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.update_event.side_effect = EventNotFoundException(event_id)
        payload = CalendarEventUpdate(title="Updated")
        with pytest.raises(HTTPException) as exc_info:
            await controller.update_user_event(user_id, event_id, payload)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_user_event_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        event_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.update_event.side_effect = EventAccessDeniedException(
            event_id, user_id
        )
        payload = CalendarEventUpdate(title="Updated")
        with pytest.raises(HTTPException) as exc_info:
            await controller.update_user_event(user_id, event_id, payload)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_update_user_event_validation_error(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        event_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.update_event.side_effect = CalendarValidationError("bad")
        payload = CalendarEventUpdate(title="Updated")
        with pytest.raises(HTTPException) as exc_info:
            await controller.update_user_event(user_id, event_id, payload)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_delete_user_event_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        event_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.delete_event.return_value = None

        result = await controller.delete_user_event(user_id, event_id)
        assert result["status"] == "success"
        assert "soft deleted" in result["message"]

    async def test_delete_user_event_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        event_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.delete_event.side_effect = EventNotFoundException(event_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.delete_user_event(user_id, event_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_user_event_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        event_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.delete_event.side_effect = EventAccessDeniedException(
            event_id, user_id
        )
        with pytest.raises(HTTPException) as exc_info:
            await controller.delete_user_event(user_id, event_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_get_analytics_delegates(self, controller):
        controller.service.get_analytics.return_value = {"total": 5}
        result = await controller.get_analytics(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert result["total"] == 5

    async def test_list_user_events_success(self, controller):
        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        mock_occurrence = MagicMock(spec=CalendarOccurrenceResponse)
        controller.service.list_events.return_value = [mock_occurrence]

        result = await controller.list_user_events(user_id, start, end, None, None, None)
        assert result == [mock_occurrence]

    async def test_list_user_events_validation_error(self, controller):
        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        controller.service.list_events.side_effect = CalendarValidationError("bad range")

        with pytest.raises(HTTPException) as exc_info:
            await controller.list_user_events(user_id, start, end, None, None, None)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
