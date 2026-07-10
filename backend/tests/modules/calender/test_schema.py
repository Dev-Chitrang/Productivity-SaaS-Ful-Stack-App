import uuid
from datetime import datetime, timezone, timedelta
import pytest
from pydantic import ValidationError
from app.modules.calender.enums import EventType, EventColor, RecurrenceFrequency
from app.modules.calender.schema import (
    CalendarEventBase,
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarEventResponse,
    CalendarOccurrenceResponse,
)
from app.modules.calender.constants import MIN_RECURRENCE_INTERVAL, MAX_TITLE_LENGTH


class TestCalendarEventBase:
    def test_valid_base(self):
        now = datetime.now(timezone.utc)
        data = {
            "title": "Team Meeting",
            "description": "Weekly sync",
            "event_type": EventType.MEETING,
            "color": EventColor.BLUE,
            "start_time": now,
            "end_time": now + timedelta(hours=1),
            "timezone": "UTC",
            "is_all_day": False,
            "location": "Room 1",
            "recurrence_frequency": RecurrenceFrequency.WEEKLY,
            "recurrence_interval": 1,
            "recurrence_end_date": None,
        }
        model = CalendarEventBase(**data)
        assert model.title == "Team Meeting"
        assert model.event_type == EventType.MEETING
        assert model.color == EventColor.BLUE

    def test_title_max_length(self):
        now = datetime.now(timezone.utc)
        title = "a" * MAX_TITLE_LENGTH
        data = {
            "title": title,
            "start_time": now,
            "end_time": now + timedelta(hours=1),
        }
        model = CalendarEventBase(**data)
        assert len(model.title) == MAX_TITLE_LENGTH

    def test_title_exceeds_max_length(self):
        now = datetime.now(timezone.utc)
        title = "a" * (MAX_TITLE_LENGTH + 1)
        with pytest.raises(ValidationError):
            CalendarEventBase(
                title=title,
                start_time=now,
                end_time=now + timedelta(hours=1),
            )

    def test_empty_title_raises(self):
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            CalendarEventBase(
                title="   ",
                start_time=now,
                end_time=now + timedelta(hours=1),
            )

    def test_title_strips_whitespace(self):
        now = datetime.now(timezone.utc)
        model = CalendarEventBase(
            title="  Meeting  ",
            start_time=now,
            end_time=now + timedelta(hours=1),
        )
        assert model.title == "Meeting"

    def test_invalid_timezone_raises(self):
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            CalendarEventBase(
                title="Meeting",
                start_time=now,
                end_time=now + timedelta(hours=1),
                timezone="Invalid/Timezone",
            )

    def test_valid_timezone_accepted(self):
        now = datetime.now(timezone.utc)
        model = CalendarEventBase(
            title="Meeting",
            start_time=now,
            end_time=now + timedelta(hours=1),
            timezone="America/New_York",
        )
        assert model.timezone == "America/New_York"

    def test_recurrence_interval_below_min_raises(self):
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            CalendarEventBase(
                title="Meeting",
                start_time=now,
                end_time=now + timedelta(hours=1),
                recurrence_interval=0,
            )

    def test_recurrence_interval_min_ok(self):
        now = datetime.now(timezone.utc)
        model = CalendarEventBase(
            title="Meeting",
            start_time=now,
            end_time=now + timedelta(hours=1),
            recurrence_interval=MIN_RECURRENCE_INTERVAL,
        )
        assert model.recurrence_interval == MIN_RECURRENCE_INTERVAL


class TestCalendarEventCreate:
    def test_valid_create(self):
        now = datetime.now(timezone.utc)
        data = {
            "title": "Meeting",
            "start_time": now,
            "end_time": now + timedelta(hours=1),
        }
        model = CalendarEventCreate(**data)
        assert model.title == "Meeting"

    def test_start_after_end_raises(self):
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            CalendarEventCreate(
                title="Meeting",
                start_time=now + timedelta(hours=2),
                end_time=now + timedelta(hours=1),
            )

    def test_start_equals_end_raises(self):
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            CalendarEventCreate(
                title="Meeting",
                start_time=now,
                end_time=now,
            )

    def test_recurrence_end_before_start_raises(self):
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            CalendarEventCreate(
                title="Meeting",
                start_time=now,
                end_time=now + timedelta(hours=1),
                recurrence_end_date=now - timedelta(days=1),
            )

    def test_recurrence_end_after_start_ok(self):
        now = datetime.now(timezone.utc)
        model = CalendarEventCreate(
            title="Meeting",
            start_time=now,
            end_time=now + timedelta(hours=1),
            recurrence_end_date=now + timedelta(days=30),
        )
        assert model.recurrence_end_date is not None

    def test_defaults(self):
        now = datetime.now(timezone.utc)
        model = CalendarEventCreate(
            title="Meeting",
            start_time=now,
            end_time=now + timedelta(hours=1),
        )
        assert model.event_type == EventType.PERSONAL
        assert model.color == EventColor.BLUE
        assert model.timezone == "UTC"
        assert model.is_all_day is False
        assert model.location is None
        assert model.recurrence_frequency is None
        assert model.recurrence_interval is None
        assert model.recurrence_end_date is None


class TestCalendarEventUpdate:
    def test_valid_partial_update(self):
        now = datetime.now(timezone.utc)
        model = CalendarEventUpdate(
            title="Updated Meeting",
            start_time=now,
            end_time=now + timedelta(hours=1),
        )
        assert model.title == "Updated Meeting"
        assert model.description is None

    def test_start_after_end_raises_when_both_provided(self):
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            CalendarEventUpdate(
                start_time=now + timedelta(hours=2),
                end_time=now + timedelta(hours=1),
            )

    def test_start_equals_end_raises_when_both_provided(self):
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            CalendarEventUpdate(
                start_time=now,
                end_time=now,
            )

    def test_only_start_provided_is_ok(self):
        now = datetime.now(timezone.utc)
        model = CalendarEventUpdate(start_time=now + timedelta(hours=2))
        assert model.start_time is not None
        assert model.end_time is None

    def test_only_end_provided_is_ok(self):
        now = datetime.now(timezone.utc)
        model = CalendarEventUpdate(end_time=now + timedelta(hours=2))
        assert model.start_time is None
        assert model.end_time is not None

    def test_empty_title_strips_whitespace(self):
        model = CalendarEventUpdate(title="  Updated  ")
        assert model.title == "Updated"

    def test_invalid_timezone_raises(self):
        with pytest.raises(ValidationError):
            CalendarEventUpdate(timezone="Invalid/Timezone")

    def test_none_timezone_accepted(self):
        model = CalendarEventUpdate(timezone=None)
        assert model.timezone is None


class TestCalendarEventResponse:
    def test_valid_response(self):
        event_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        now = datetime.now(timezone.utc)
        data = {
            "id": event_id,
            "user_id": user_id,
            "title": "Meeting",
            "description": "Desc",
            "event_type": EventType.MEETING,
            "color": EventColor.BLUE,
            "start_time": now,
            "end_time": now + timedelta(hours=1),
            "timezone": "UTC",
            "is_all_day": False,
            "location": "Room",
            "created_at": now,
            "updated_at": now,
        }
        model = CalendarEventResponse(**data)
        assert model.id == event_id
        assert model.user_id == user_id
        assert model.title == "Meeting"

    def test_from_attributes_config(self):
        assert CalendarEventResponse.model_config.get("from_attributes") is True


class TestCalendarOccurrenceResponse:
    def test_valid_occurrence(self):
        event_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        now = datetime.now(timezone.utc)
        data = {
            "id": event_id,
            "title": "Meeting",
            "description": "Desc",
            "event_type": EventType.MEETING,
            "color": EventColor.BLUE,
            "start_time": now,
            "end_time": now + timedelta(hours=1),
            "timezone": "UTC",
            "is_all_day": False,
            "location": "Room",
            "is_recurring": True,
            "recurrence_frequency": RecurrenceFrequency.WEEKLY,
            "recurrence_interval": 1,
            "recurrence_end_date": None,
        }
        model = CalendarOccurrenceResponse(**data)
        assert model.id == event_id
        assert model.is_recurring is True
        assert model.recurrence_frequency == RecurrenceFrequency.WEEKLY

    def test_default_is_recurring_false(self):
        event_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        now = datetime.now(timezone.utc)
        data = {
            "id": event_id,
            "title": "Meeting",
            "description": None,
            "event_type": EventType.MEETING,
            "color": EventColor.BLUE,
            "start_time": now,
            "end_time": now + timedelta(hours=1),
            "timezone": "UTC",
            "is_all_day": False,
            "location": None,
        }
        model = CalendarOccurrenceResponse(**data)
        assert model.is_recurring is False
        assert model.recurrence_frequency is None

    def test_from_attributes_config(self):
        assert CalendarOccurrenceResponse.model_config.get("from_attributes") is True
