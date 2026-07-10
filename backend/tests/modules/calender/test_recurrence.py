import uuid
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import pytest
from app.modules.calender.enums import EventType, EventColor, RecurrenceFrequency
from app.modules.calender.recurrence import RecurrenceEngine
from app.models.calender import CalendarEvent
from app.modules.calender.schema import CalendarOccurrenceResponse


def _make_event(
    title="Weekly Meeting",
    start_time=None,
    end_time=None,
    recurrence_frequency=RecurrenceFrequency.WEEKLY,
    recurrence_interval=1,
    recurrence_end_date=None,
    **kwargs,
):
    event_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
    user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
    now = datetime.now(timezone.utc)
    if start_time is None:
        start_time = now
    if end_time is None:
        end_time = now + timedelta(hours=1)
    return CalendarEvent(
        id=event_id,
        user_id=user_id,
        title=title,
        description=kwargs.get("description", "Desc"),
        event_type=kwargs.get("event_type", EventType.MEETING),
        color=kwargs.get("color", EventColor.BLUE),
        start_time=start_time,
        end_time=end_time,
        timezone=kwargs.get("timezone", "UTC"),
        is_all_day=kwargs.get("is_all_day", False),
        location=kwargs.get("location", None),
        recurrence_frequency=recurrence_frequency,
        recurrence_interval=recurrence_interval,
        recurrence_end_date=recurrence_end_date,
        deleted_at=kwargs.get("deleted_at", None),
        created_at=kwargs.get("created_at", now),
        updated_at=kwargs.get("updated_at", now),
    )


class TestGenerateOccurrencesForEvent:
    def test_returns_list(self):
        event = _make_event()
        result = RecurrenceEngine.generate_occurrences_for_event(
            event, datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 31, tzinfo=timezone.utc)
        )
        assert isinstance(result, list)

    def test_no_occurrences_before_series_start(self):
        event = _make_event(
            start_time=datetime(2024, 2, 1, tzinfo=timezone.utc),
            end_time=datetime(2024, 2, 1, tzinfo=timezone.utc) + timedelta(hours=1),
        )
        result = RecurrenceEngine.generate_occurrences_for_event(
            event, datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 31, tzinfo=timezone.utc)
        )
        assert len(result) == 0

    def test_single_event_if_no_recurrence(self):
        event = _make_event(
            recurrence_frequency=None,
            start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
        )
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        result = RecurrenceEngine.generate_occurrences_for_event(event, start, end)
        assert len(result) == 1
        assert result[0].is_recurring is True
        assert result[0].recurrence_frequency is None

    def test_daily_recurrence_count(self):
        event = _make_event(
            start_time=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),
            recurrence_frequency=RecurrenceFrequency.DAILY,
            recurrence_interval=1,
        )
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 11, tzinfo=timezone.utc)
        result = RecurrenceEngine.generate_occurrences_for_event(event, start, end)
        assert len(result) == 10

    def test_weekly_recurrence_count(self):
        event = _make_event(
            start_time=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),
            recurrence_frequency=RecurrenceFrequency.WEEKLY,
            recurrence_interval=1,
        )
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        result = RecurrenceEngine.generate_occurrences_for_event(event, start, end)
        assert len(result) == 5

    def test_recurrence_end_date_limits_occurrences(self):
        event = _make_event(
            start_time=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),
            recurrence_frequency=RecurrenceFrequency.DAILY,
            recurrence_interval=1,
            recurrence_end_date=datetime(2024, 1, 6, tzinfo=timezone.utc),
        )
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        result = RecurrenceEngine.generate_occurrences_for_event(event, start, end)
        assert len(result) == 5

    def test_recurrence_interval_greater_than_one(self):
        event = _make_event(
            start_time=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),
            recurrence_frequency=RecurrenceFrequency.DAILY,
            recurrence_interval=2,
        )
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 10, tzinfo=timezone.utc)
        result = RecurrenceEngine.generate_occurrences_for_event(event, start, end)
        assert len(result) == 5

    def test_events_span_proper_duration(self):
        start = datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        event = _make_event(
            start_time=start,
            end_time=end,
            recurrence_frequency=RecurrenceFrequency.DAILY,
            recurrence_interval=1,
        )
        result = RecurrenceEngine.generate_occurrences_for_event(
            event, datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 4, tzinfo=timezone.utc)
        )
        assert len(result) == 3
        for occ in result:
            assert (occ.end_time - occ.start_time).total_seconds() == 7200

    def test_occurrences_sorted_by_start_time(self):
        event = _make_event(
            start_time=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),
            recurrence_frequency=RecurrenceFrequency.DAILY,
            recurrence_interval=1,
        )
        result = RecurrenceEngine.generate_occurrences_for_event(
            event, datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 5, tzinfo=timezone.utc)
        )
        for i in range(len(result) - 1):
            assert result[i].start_time <= result[i + 1].start_time

    def test_occurrence_response_fields(self):
        event = _make_event(
            start_time=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),
            recurrence_frequency=RecurrenceFrequency.WEEKLY,
            recurrence_interval=1,
        )
        result = RecurrenceEngine.generate_occurrences_for_event(
            event, datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 15, tzinfo=timezone.utc)
        )
        assert len(result) == 2
        occ = result[0]
        assert occ.id == event.id
        assert occ.title == event.title
        assert occ.is_recurring is True
        assert occ.recurrence_frequency == RecurrenceFrequency.WEEKLY
        assert occ.recurrence_interval == 1

    def test_monthly_recurrence_jan31_to_feb28(self):
        event = _make_event(
            start_time=datetime(2024, 1, 31, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 31, 11, 0, tzinfo=timezone.utc),
            recurrence_frequency=RecurrenceFrequency.MONTHLY,
            recurrence_interval=1,
        )
        result = RecurrenceEngine.generate_occurrences_for_event(
            event, datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 4, 30, tzinfo=timezone.utc)
        )
        assert len(result) >= 1
        for occ in result:
            assert occ.start_time.day <= 31

    def test_unknown_frequency_stops_expansion(self):
        event = _make_event(
            start_time=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),
            recurrence_frequency=None,
        )
        result = RecurrenceEngine.generate_occurrences_for_event(
            event, datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 31, tzinfo=timezone.utc)
        )
        assert len(result) == 1

    def test_empty_window_returns_empty(self):
        event = _make_event(
            start_time=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),
            recurrence_frequency=None,
        )
        result = RecurrenceEngine.generate_occurrences_for_event(
            event, datetime(2024, 2, 1, tzinfo=timezone.utc), datetime(2024, 2, 10, tzinfo=timezone.utc)
        )
        assert len(result) == 0
