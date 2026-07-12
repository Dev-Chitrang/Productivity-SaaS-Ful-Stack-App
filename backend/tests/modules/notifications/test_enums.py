import pytest
from app.modules.notifications.enums import NotificationType
from app.modules.notifications.constants import (
    MEETING_REMINDER_WINDOW_MINUTES,
    NOTIFICATION_PAGE_SIZE,
    MAX_NOTIFICATION_SEARCH_LENGTH,
)


class TestNotificationEnums:
    def test_notification_type_values(self):
        assert NotificationType.MEETING_REMINDER.value == "MEETING_REMINDER"

    def test_notification_type_count(self):
        assert len(NotificationType) == 1


class TestConstants:
    def test_reminder_window(self):
        assert MEETING_REMINDER_WINDOW_MINUTES == 10

    def test_page_size(self):
        assert NOTIFICATION_PAGE_SIZE == 20

    def test_max_search_length(self):
        assert MAX_NOTIFICATION_SEARCH_LENGTH == 200
