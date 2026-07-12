import uuid
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.calender.enums import EventType, EventColor, RecurrenceFrequency
from app.modules.calender.repository import CalendarRepository
from app.models.calender import CalendarEvent


@pytest.fixture
def repo():
    db = AsyncMock(spec=AsyncSession)
    return CalendarRepository(db)


def _make_event(**kwargs):
    now = datetime.now(timezone.utc)
    return CalendarEvent(
        id=kwargs.get("id", uuid.UUID("12345678-1234-5678-1234-567812345678")),
        user_id=kwargs.get("user_id", uuid.UUID("87654321-4321-8765-4321-876543218765")),
        title=kwargs.get("title", "Test Event"),
        description=kwargs.get("description", "Desc"),
        event_type=kwargs.get("event_type", EventType.MEETING),
        color=kwargs.get("color", EventColor.BLUE),
        start_time=kwargs.get("start_time", now),
        end_time=kwargs.get("end_time", now + timedelta(hours=1)),
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


class TestCalendarRepositoryCreate:
    async def test_create_success(self, repo):
        event = _make_event()
        result = await repo.create(event.user_id, {"title": "Test Event"})
        assert result.user_id == event.user_id
        repo.db.add.assert_called_once()
        repo.db.flush.assert_called_once()

    async def test_create_rollback_on_exception(self, repo):
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.create(uuid.UUID("12345678-1234-5678-1234-567812345678"), {"title": "Test"})
        repo.db.rollback.assert_called_once()


class TestCalendarRepositoryGetById:
    async def test_get_by_id_found(self, repo):
        event = _make_event()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = event
        repo.db.execute.return_value = result_mock

        found = await repo.get_by_id(event.id)
        assert found == event
        repo.db.execute.assert_called_once()

    async def test_get_by_id_not_found(self, repo):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        repo.db.execute.return_value = result_mock

        found = await repo.get_by_id(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert found is None

    async def test_get_by_id_excludes_soft_deleted(self, repo):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        repo.db.execute.return_value = result_mock

        await repo.get_by_id(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        stmt = repo.db.execute.call_args[0][0]
        assert "deleted_at" in str(stmt)


class TestCalendarRepositoryUpdate:
    async def test_update_success(self, repo):
        event = _make_event()
        update_data = {"title": "Updated Title", "location": "Room 2"}
        result = await repo.update(event, update_data)
        assert result.title == "Updated Title"
        assert result.location == "Room 2"
        repo.db.add.assert_called_once_with(event)
        repo.db.flush.assert_called_once()

    async def test_update_partial_fields(self, repo):
        event = _make_event()
        update_data = {"title": "Updated Title"}
        result = await repo.update(event, update_data)
        assert result.title == "Updated Title"
        assert result.location is None

    async def test_update_rollback_on_exception(self, repo):
        event = _make_event()
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.update(event, {"title": "Updated"})
        repo.db.rollback.assert_called_once()


class TestCalendarRepositorySoftDelete:
    async def test_soft_delete_success(self, repo):
        event = _make_event(deleted_at=None)
        now = datetime.utcnow()
        result = await repo.soft_delete(event)
        assert result is None
        assert event.deleted_at is not None
        assert event.deleted_at >= now - timedelta(seconds=2)
        repo.db.add.assert_called_once_with(event)
        repo.db.flush.assert_called_once()

    async def test_soft_delete_rollback_on_exception(self, repo):
        event = _make_event()
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.soft_delete(event)
        repo.db.rollback.assert_called_once()


class TestCalendarRepositoryGetAnalytics:
    async def test_get_analytics_returns_dict(self, repo):
        repo.db.scalar.return_value = 5
        repo.db.execute.return_value = MagicMock()

        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        result = await repo.get_analytics(user_id)

        assert isinstance(result, dict)
        assert "total" in result
        assert "today" in result
        assert "upcoming" in result
        assert "monthly_events" in result
        assert "past_events" in result
        assert "future_events" in result
        assert "next_events" in result

    async def test_get_analytics_counts(self, repo):
        repo.db.scalar.side_effect = [10, 2, 5, 3, 7]
        repo.db.execute.return_value = MagicMock()

        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        result = await repo.get_analytics(user_id)

        assert result["total"] == 10
        assert result["today"] == 2
        assert result["upcoming"] == 5
        assert result["past_events"] == 3
        assert result["future_events"] == 7

    async def test_get_analytics_next_events_structure(self, repo):
        repo.db.scalar.return_value = 0
        mock_row = MagicMock()
        mock_row.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_row.title = "Next Event"
        mock_row.start_time = datetime.now(timezone.utc)
        mock_row.end_time = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_row.color = EventColor.BLUE
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = [mock_row]

        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        result = await repo.get_analytics(user_id)

        assert len(result["next_events"]) == 1
        assert result["next_events"][0]["title"] == "Next Event"
        assert result["next_events"][0]["color"] == "BLUE"


class TestCalendarRepositoryListEvents:
    async def test_list_events_returns_sequence(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        result = await repo.list_events(user_id, start, end)
        assert isinstance(result, list)

    async def test_list_events_filters_by_user(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        await repo.list_events(user_id, start, end)
        stmt = repo.db.execute.call_args[0][0]
        assert "user_id" in str(stmt)

    async def test_list_events_excludes_soft_deleted(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        await repo.list_events(user_id, start, end)
        stmt = repo.db.execute.call_args[0][0]
        assert "deleted_at" in str(stmt)

    async def test_list_events_search_query(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        await repo.list_events(user_id, start, end, search_query="meeting")
        stmt = repo.db.execute.call_args[0][0]
        assert "like" in str(stmt).lower() or "ilike" in str(stmt).lower()

    async def test_list_events_event_type_filter(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        await repo.list_events(user_id, start, end, event_type=EventType.MEETING)
        stmt = repo.db.execute.call_args[0][0]
        assert "event_type" in str(stmt)

    async def test_list_events_color_filter(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        await repo.list_events(user_id, start, end, color=EventColor.RED)
        stmt = repo.db.execute.call_args[0][0]
        assert "color" in str(stmt)

    async def test_list_events_ordered_by_start_time(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        await repo.list_events(user_id, start, end)
        stmt = repo.db.execute.call_args[0][0]
        assert "start_time" in str(stmt)
