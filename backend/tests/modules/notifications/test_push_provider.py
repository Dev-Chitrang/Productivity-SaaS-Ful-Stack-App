import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.modules.notifications.push_provider import PushNotificationProvider, PushSubscriptionExpiredException


class TestPushNotificationProvider:
    def test_init(self):
        provider = PushNotificationProvider()
        assert provider is not None

    @patch("app.modules.notifications.push_provider.webpush")
    def test_send_push_success(self, mock_web_push):
        mock_web_push.return_value = None
        provider = PushNotificationProvider()
        result = provider.send_push(
            subscription_info={"endpoint": "https://example.com", "keys": {"p256dh": "key", "auth": "auth"}},
            title="Test",
            body="Body",
            url="/dashboard",
        )
        assert result is True
        mock_web_push.assert_called_once()

    @patch("app.modules.notifications.push_provider.webpush")
    def test_send_push_404_raises_expired(self, mock_web_push):
        from pywebpush import WebPushException
        mock_web_push.side_effect = WebPushException("404 Gone")
        provider = PushNotificationProvider()
        with pytest.raises(PushSubscriptionExpiredException):
            provider.send_push(
                subscription_info={"endpoint": "https://example.com", "keys": {}},
                title="Test",
                body="Body",
            )

    @patch("app.modules.notifications.push_provider.webpush")
    def test_send_push_410_raises_expired(self, mock_web_push):
        from pywebpush import WebPushException
        mock_web_push.side_effect = WebPushException("410 Gone")
        provider = PushNotificationProvider()
        with pytest.raises(PushSubscriptionExpiredException):
            provider.send_push(
                subscription_info={"endpoint": "https://example.com", "keys": {}},
                title="Test",
                body="Body",
            )

    @patch("app.modules.notifications.push_provider.webpush")
    def test_send_push_general_exception_returns_false(self, mock_web_push):
        mock_web_push.side_effect = Exception("Network error")
        provider = PushNotificationProvider()
        result = provider.send_push(
            subscription_info={"endpoint": "https://example.com", "keys": {}},
            title="Test",
            body="Body",
        )
        assert result is False
