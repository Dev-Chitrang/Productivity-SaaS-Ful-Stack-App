import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.modules.calender.enums import EventType, EventColor, RecurrenceFrequency
from app.modules.calender.exceptions import (
    EventNotFoundException,
    EventAccessDeniedException,
    CalendarValidationError,
)
from app.modules.calender.recurrence import RecurrenceEngine
from app.modules.calender.repository import CalendarRepository
from app.modules.calender.service import CalendarService
from app.modules.calender.schema import CalendarEventCreate, CalendarEventUpdate, CalendarOccurrenceResponse
from app.models.calender import CalendarEvent


@pytest.fixture
def repo():
    return MagicMock(spec=CalendarRepository)


@pytest.fixture
def redis_mock():
    return AsyncMock()


@pytest.fixture
def service(repo, redis_mock):
    return CalendarService(repo, attachment_service=None)


def _make_event(**kwargs):
    now = datetime.now(timezone.utc)
    return CalendarEvent(
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
        recurrence_frequency=kwargs.get("recurrence_frequency", None),
        recurrence_interval=kwargs.get("recurrence_interval", None),
        recurrence_end_date=kwargs.get("recurrence_end_date", None),
        deleted_at=kwargs.get("deleted_at", None),
        created_at=kwargs.get("created_at", now),
        updated_at=kwargs.get("updated_at", now),
    )


class TestCreateEvent:
    async def test_create_event_success(self, service, repo):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        now = datetime.now(timezone.utc)
        payload = CalendarEventCreate(
            title="New Meeting",
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=1),
        )
        repo.create.return_value = _make_event(title="New Meeting")

        result = await service.create_event(user_id, payload)
        assert result.title == "New Meeting"
        repo.create.assert_called_once()

    async def test_create_event_in_past_raises(self, service):
        now = datetime.now(timezone.utc)
        payload = CalendarEventCreate(
            title="Past Event",
            start_time=now - timedelta(hours=1),
            end_time=now,
        )
        with pytest.raises(CalendarValidationError, match="past"):
            await service.create_event(uuid.UUID("87654321-4321-8765-4321-876543218765"), payload)

    async def test_create_event_start_after_end_raises(self, service):
        now = datetime.now(timezone.utc)
        payload = CalendarEventCreate.model_construct(
            title="Bad Event",
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=1),
        )
        with pytest.raises(CalendarValidationError, match="Event start time must be before end time."):
            await service.create_event(uuid.UUID("87654321-4321-8765-4321-876543218765"), payload)

    async def test_create_event_start_equals_end_raises(self, service):
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        payload = CalendarEventCreate.model_construct(
            title="Bad Event",
            start_time=future,
            end_time=future,
        )
        with pytest.raises(CalendarValidationError, match="Event start time must be before end time."):
            await service.create_event(uuid.UUID("87654321-4321-8765-4321-876543218765"), payload)


class TestGetEvent:
    async def test_get_event_success(self, service, repo):
        event = _make_event()
        repo.get_by_id.return_value = event

        result = await service.get_event(event.user_id, event.id)
        assert result == event
        repo.get_by_id.assert_called_once_with(event.id)

    async def test_get_event_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(EventNotFoundException):
            await service.get_event(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"))

    async def test_get_event_access_denied(self, service, repo):
        event = _make_event(user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"))
        repo.get_by_id.return_value = event
        with pytest.raises(EventAccessDeniedException):
            await service.get_event(uuid.UUID("87654321-4321-8765-4321-876543218765"), event.id)


class TestUpdateEvent:
    async def test_update_event_success(self, service, repo):
        event = _make_event()
        repo.get_by_id.return_value = event
        def _update_side_effect(event_obj, update_data):
            for key, value in update_data.items():
                setattr(event_obj, key, value)
            return event_obj
        repo.update.side_effect = _update_side_effect

        payload = CalendarEventUpdate(title="Updated Title")
        result = await service.update_event(event.user_id, event.id, payload)
        assert result.title == "Updated Title"
        repo.update.assert_called_once()

    async def test_update_event_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        payload = CalendarEventUpdate(title="Updated Title")
        with pytest.raises(EventNotFoundException):
            await service.update_event(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"), payload)

    async def test_update_event_moves_to_past_raises(self, service, repo):
        event = _make_event()
        repo.get_by_id.return_value = event

        past = datetime.now(timezone.utc) - timedelta(hours=1)
        payload = CalendarEventUpdate(start_time=past)
        with pytest.raises(CalendarValidationError, match="past"):
            await service.update_event(event.user_id, event.id, payload)

    async def test_update_event_start_after_end_raises(self, service, repo):
        event = _make_event()
        repo.get_by_id.return_value = event

        now = datetime.now(timezone.utc)
        payload = CalendarEventUpdate.model_construct(
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=1),
        )
        with pytest.raises(CalendarValidationError, match="Event start time must be before end time"):
            await service.update_event(event.user_id, event.id, payload)

    async def test_update_event_recurrence_end_before_start_raises(self, service, repo):
        event = _make_event(
            start_time=datetime(2024, 6, 1, tzinfo=timezone.utc),
            end_time=datetime(2024, 6, 1, tzinfo=timezone.utc) + timedelta(hours=1),
            recurrence_frequency=RecurrenceFrequency.DAILY,
        )
        repo.get_by_id.return_value = event

        payload = CalendarEventUpdate(
            recurrence_end_date=datetime(2024, 5, 1, tzinfo=timezone.utc)
        )
        with pytest.raises(CalendarValidationError, match="Recurrence end date cannot terminate prior"):
            await service.update_event(event.user_id, event.id, payload)


class TestDeleteEvent:
    async def test_delete_event_success_without_attachments(self, service, repo):
        event = _make_event()
        repo.get_by_id.return_value = event

        await service.delete_event(event.user_id, event.id)
        repo.soft_delete.assert_called_once_with(event)

    async def test_delete_event_cascades_to_attachments(self, service, repo):
        event = _make_event()
        repo.get_by_id.return_value = event
        attachment_service = AsyncMock()
        service_with_att = CalendarService(repo, attachment_service=attachment_service)

        await service_with_att.delete_event(event.user_id, event.id)
        repo.soft_delete.assert_called_once_with(event)

    async def test_delete_event_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(EventNotFoundException):
            await service.delete_event(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"))


class TestGetAnalytics:
    async def test_get_analytics_delegates_to_repo(self, service, repo):
        repo.get_analytics.return_value = {"total": 5}
        result = await service.get_analytics(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert result["total"] == 5
        repo.get_analytics.assert_called_once()


class TestListEvents:
    async def test_list_events_success(self, service, repo):
        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        event = _make_event()
        repo.list_events.return_value = [event]

        result = await service.list_events(user_id, start, end)
        assert len(result) == 1
        assert result[0].is_recurring is False
        repo.list_events.assert_called_once_with(
            user_id=user_id,
            range_start=start,
            range_end=end,
            search_query=None,
            event_type=None,
            color=None,
        )

    async def test_list_events_range_start_equals_end_raises(self, service):
        now = datetime.now(timezone.utc)
        with pytest.raises(CalendarValidationError, match="range_start must be chronologically before range_end"):
            await service.list_events(
                uuid.UUID("12345678-1234-5678-1234-567812345678"),
                now,
                now,
            )

    async def test_list_events_range_start_after_end_raises(self, service):
        now = datetime.now(timezone.utc)
        with pytest.raises(CalendarValidationError, match="range_start must be chronologically before range_end"):
            await service.list_events(
                uuid.UUID("12345678-1234-5678-1234-567812345678"),
                now + timedelta(hours=1),
                now,
            )

    async def test_list_events_recurring_expanded(self, service, repo):
        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        event = _make_event(
            recurrence_frequency=RecurrenceFrequency.DAILY,
            recurrence_interval=1,
        )
        repo.list_events.return_value = [event]

        with patch.object(RecurrenceEngine, "generate_occurrences_for_event") as mock_gen:
            mock_gen.return_value = [
                CalendarOccurrenceResponse(
                    id=event.id,
                    title=event.title,
                    description=event.description,
                    event_type=event.event_type,
                    color=event.color,
                    start_time=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
                    end_time=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),
                    timezone="UTC",
                    is_all_day=False,
                    location=None,
                    is_recurring=True,
                )
            ]
            result = await service.list_events(user_id, start, end)
            mock_gen.assert_called_once_with(event, start, end)

    async def test_list_events_non_recurring_passthrough(self, service, repo):
        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        event = _make_event(recurrence_frequency=None)
        repo.list_events.return_value = [event]

        result = await service.list_events(user_id, start, end)
        assert len(result) == 1
        assert result[0].is_recurring is False
        assert result[0].id == event.id

    async def test_list_events_sorted_by_start_time(self, service, repo):
        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        repo.list_events.return_value = []

        result = await service.list_events(user_id, start, end)
        result.append(CalendarOccurrenceResponse(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Early",
            description=None,
            event_type=EventType.PERSONAL,
            color=EventColor.BLUE,
            start_time=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),
            timezone="UTC",
            is_all_day=False,
            location=None,
        ))
        result.append(CalendarOccurrenceResponse(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Late",
            description=None,
            event_type=EventType.PERSONAL,
            color=EventColor.BLUE,
            start_time=datetime(2024, 1, 2, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 2, 11, 0, tzinfo=timezone.utc),
            timezone="UTC",
            is_all_day=False,
            location=None,
        ))
        assert result[0].title == "Early"
        assert result[1].title == "Late"
