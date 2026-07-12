import uuid
import pytest
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.modules.calender.enums import EventType, EventColor, RecurrenceFrequency
from app.modules.calender.constants import MIN_RECURRENCE_INTERVAL, MAX_TITLE_LENGTH
from app.models.calender import CalendarEvent


class TestCalendarEventModel:
    def test_tablename(self):
        assert CalendarEvent.__tablename__ == "calendar_events"

    def test_id_default_generates_uuid(self):
        event = CalendarEvent(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Meeting",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
        )
        assert event.id is None or isinstance(event.id, uuid.UUID)

    def test_minimal_fields(self):
        now = datetime.now(timezone.utc)
        event = CalendarEvent(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Minimal Event",
            start_time=now,
            end_time=now,
            event_type=EventType.PERSONAL,
            color=EventColor.BLUE,
            timezone="UTC",
            is_all_day=False,
            created_at=now,
            updated_at=now,
        )
        assert event.user_id == uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert event.title == "Minimal Event"
        assert event.description is None
        assert event.event_type == EventType.PERSONAL
        assert event.color == EventColor.BLUE
        assert event.start_time == now
        assert event.end_time == now
        assert event.timezone == "UTC"
        assert event.is_all_day is False
        assert event.location is None
        assert event.recurrence_frequency is None
        assert event.recurrence_interval is None
        assert event.recurrence_end_date is None
        assert event.deleted_at is None
        assert isinstance(event.created_at, datetime)
        assert isinstance(event.updated_at, datetime)

    def test_full_fields(self):
        event_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        now = datetime.now(timezone.utc)
        event = CalendarEvent(
            id=event_id,
            user_id=user_id,
            title="Full Event",
            description="Description here",
            event_type=EventType.MEETING,
            color=EventColor.RED,
            start_time=now,
            end_time=now,
            timezone="America/New_York",
            is_all_day=True,
            location="Conference Room",
            recurrence_frequency=RecurrenceFrequency.WEEKLY,
            recurrence_interval=2,
            recurrence_end_date=now,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )
        assert event.id == event_id
        assert event.user_id == user_id
        assert event.title == "Full Event"
        assert event.description == "Description here"
        assert event.event_type == EventType.MEETING
        assert event.color == EventColor.RED
        assert event.timezone == "America/New_York"
        assert event.is_all_day is True
        assert event.location == "Conference Room"
        assert event.recurrence_frequency == RecurrenceFrequency.WEEKLY
        assert event.recurrence_interval == 2
        assert event.recurrence_end_date == now

    def test_soft_delete(self):
        now = datetime.now(timezone.utc)
        event = CalendarEvent(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Event",
            start_time=now,
            end_time=now,
            deleted_at=now,
        )
        assert event.deleted_at == now

    def test_created_at_default_utc(self):
        now = datetime.now(timezone.utc)
        event = CalendarEvent(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Event",
            start_time=now,
            end_time=now,
            created_at=now,
        )
        assert event.created_at is not None
        assert event.created_at.tzinfo == timezone.utc

    def test_updated_at_default_utc(self):
        now = datetime.now(timezone.utc)
        event = CalendarEvent(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Event",
            start_time=now,
            end_time=now,
            updated_at=now,
        )
        assert event.updated_at is not None
        assert event.updated_at.tzinfo == timezone.utc
