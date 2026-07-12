import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.modules.notifications.controller import NotificationController
from app.modules.notifications.enums import NotificationType
from app.modules.notifications.exceptions import NotificationNotFoundException, NotificationAccessDeniedException
from app.modules.notifications.schemas import PushSubscriptionCreate


@pytest.fixture
def mock_service():
    return AsyncMock()


@pytest.fixture
def controller(mock_service):
    return NotificationController(mock_service)


class TestRegisterSubscription:
    @pytest.mark.asyncio
    async def test_returns_subscription_response(self, controller, mock_service, sample_user_id):
        payload = PushSubscriptionCreate(
            endpoint="https://example.com/push",
            p256dh="key",
            auth="auth",
        )
        mock_service.register_subscription = AsyncMock(
            return_value=MagicMock(id=uuid4(), user_id=sample_user_id, endpoint="https://example.com/push", browser=None, created_at="2025-01-01T00:00:00Z")
        )
        result = await controller.register_subscription(sample_user_id, payload)
        assert "id" in result or hasattr(result, "id")


class TestRemoveSubscription:
    @pytest.mark.asyncio
    async def test_returns_removed(self, controller, mock_service):
        mock_service.remove_subscription = AsyncMock(return_value=True)
        result = await controller.remove_subscription("https://example.com/push")
        assert result["removed"] is True


class TestGetNotification:
    @pytest.mark.asyncio
    async def test_raises_404(self, controller, mock_service, sample_user_id):
        mock_service.get_notification = AsyncMock(side_effect=NotificationNotFoundException(uuid4()))
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await controller.get_notification(sample_user_id, uuid4())
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_403(self, controller, mock_service, sample_user_id):
        mock_service.get_notification = AsyncMock(side_effect=NotificationAccessDeniedException(uuid4(), sample_user_id))
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await controller.get_notification(sample_user_id, uuid4())
        assert exc_info.value.status_code == 403


class TestMarkAsRead:
    @pytest.mark.asyncio
    async def test_marks_read(self, controller, mock_service, sample_user_id):
        ids = [uuid4()]
        mock_service.mark_as_read = AsyncMock()
        result = await controller.mark_as_read(sample_user_id, ids)
        assert result["marked"] == 1


class TestGetUnreadCount:
    @pytest.mark.asyncio
    async def test_returns_count(self, controller, mock_service, sample_user_id):
        mock_service.get_unread_count = AsyncMock(return_value=3)
        result = await controller.get_unread_count(sample_user_id)
        assert result.count == 3
