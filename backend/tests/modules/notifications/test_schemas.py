import pytest
from uuid import uuid4
from app.modules.notifications.enums import NotificationType
from app.modules.notifications.schemas import (
    PushSubscriptionCreate,
    PushSubscriptionResponse,
    NotificationResponse,
    NotificationListResponse,
    NotificationMarkReadRequest,
    NotificationUnreadCountResponse,
)


class TestNotificationType:
    def test_meeting_reminder_value(self):
        assert NotificationType.MEETING_REMINDER.value == "MEETING_REMINDER"

    def test_notification_type_is_str_enum(self):
        assert issubclass(NotificationType, str)


class TestPushSubscriptionCreate:
    def test_valid_subscription(self):
        sub = PushSubscriptionCreate(
            endpoint="https://example.com/push",
            p256dh="key123",
            auth="auth123",
        )
        assert sub.endpoint == "https://example.com/push"
        assert sub.p256dh == "key123"
        assert sub.auth == "auth123"
        assert sub.browser is None

    def test_with_browser(self):
        sub = PushSubscriptionCreate(
            endpoint="https://example.com/push",
            p256dh="key123",
            auth="auth123",
            browser="Firefox",
        )
        assert sub.browser == "Firefox"


class TestNotificationResponse:
    def test_valid_response(self):
        resp = NotificationResponse(
            id=uuid4(),
            user_id=uuid4(),
            type=NotificationType.MEETING_REMINDER,
            title="Meeting Reminder",
            body="Meeting starts in 10 minutes",
            extra_data={"meeting_id": "123"},
            is_read=False,
            sent_at=None,
            created_at="2025-01-01T00:00:00Z",
        )
        assert resp.type == NotificationType.MEETING_REMINDER
        assert resp.is_read is False


class TestNotificationListResponse:
    def test_valid_list_response(self):
        resp = NotificationListResponse(
            items=[],
            total=0,
            page=1,
            page_size=20,
        )
        assert resp.total == 0
        assert resp.items == []


class TestNotificationMarkReadRequest:
    def test_valid_request(self):
        ids = [uuid4(), uuid4()]
        req = NotificationMarkReadRequest(notification_ids=ids)
        assert len(req.notification_ids) == 2


class TestNotificationUnreadCountResponse:
    def test_valid_count(self):
        resp = NotificationUnreadCountResponse(count=5)
        assert resp.count == 5
