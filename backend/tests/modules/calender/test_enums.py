import pytest
from app.modules.calender.enums import EventType, EventColor, RecurrenceFrequency


class TestEventType:
    def test_personal_value(self):
        assert EventType.PERSONAL.value == "PERSONAL"

    def test_meeting_value(self):
        assert EventType.MEETING.value == "MEETING"

    def test_reminder_value(self):
        assert EventType.REMINDER.value == "REMINDER"

    def test_all_members(self):
        assert set(EventType) == {EventType.PERSONAL, EventType.MEETING, EventType.REMINDER}

    def test_is_str_enum(self):
        assert issubclass(EventType, str)

    def test_comparison_with_string(self):
        assert EventType.PERSONAL == "PERSONAL"


class TestEventColor:
    def test_red_value(self):
        assert EventColor.RED.value == "RED"

    def test_blue_value(self):
        assert EventColor.BLUE.value == "BLUE"

    def test_green_value(self):
        assert EventColor.GREEN.value == "GREEN"

    def test_yellow_value(self):
        assert EventColor.YELLOW.value == "YELLOW"

    def test_purple_value(self):
        assert EventColor.PURPLE.value == "PURPLE"

    def test_orange_value(self):
        assert EventColor.ORANGE.value == "ORANGE"

    def test_gray_value(self):
        assert EventColor.GRAY.value == "GRAY"

    def test_all_members(self):
        expected = {
            EventColor.RED,
            EventColor.BLUE,
            EventColor.GREEN,
            EventColor.YELLOW,
            EventColor.PURPLE,
            EventColor.ORANGE,
            EventColor.GRAY,
        }
        assert set(EventColor) == expected

    def test_is_str_enum(self):
        assert issubclass(EventColor, str)

    def test_comparison_with_string(self):
        assert EventColor.BLUE == "BLUE"


class TestRecurrenceFrequency:
    def test_daily_value(self):
        assert RecurrenceFrequency.DAILY.value == "DAILY"

    def test_weekly_value(self):
        assert RecurrenceFrequency.WEEKLY.value == "WEEKLY"

    def test_monthly_value(self):
        assert RecurrenceFrequency.MONTHLY.value == "MONTHLY"

    def test_all_members(self):
        assert set(RecurrenceFrequency) == {
            RecurrenceFrequency.DAILY,
            RecurrenceFrequency.WEEKLY,
            RecurrenceFrequency.MONTHLY,
        }

    def test_is_str_enum(self):
        assert issubclass(RecurrenceFrequency, str)

    def test_comparison_with_string(self):
        assert RecurrenceFrequency.WEEKLY == "WEEKLY"
