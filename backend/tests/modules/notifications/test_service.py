import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from app.modules.notifications.service import NotificationService
from app.modules.notifications.enums import NotificationType
from app.modules.notifications.exceptions import (
    NotificationNotFoundException,
    NotificationAccessDeniedException,
)
from app.modules.notifications.schemas import PushSubscriptionCreate


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_repo):
    return NotificationService(mock_repo)


class TestRegisterSubscription:
    @pytest.mark.asyncio
    async def test_registers_subscription(self, service, mock_repo, sample_user_id):
        payload = PushSubscriptionCreate(
            endpoint="https://example.com/push",
            p256dh="key",
            auth="auth",
        )
        mock_repo.create_subscription = AsyncMock(return_value=MagicMock(id=uuid4()))

        result = await service.register_subscription(sample_user_id, payload)
        mock_repo.create_subscription.assert_called_once_with(sample_user_id, {
            "endpoint": "https://example.com/push",
            "p256dh": "key",
            "auth": "auth",
            "browser": None,
        })


class TestRemoveSubscription:
    @pytest.mark.asyncio
    async def test_removes_subscription(self, service, mock_repo):
        mock_repo.delete_subscription = AsyncMock(return_value=True)
        result = await service.remove_subscription("https://example.com/push")
        assert result is True


class TestGetNotification:
    @pytest.mark.asyncio
    async def test_raises_not_found(self, service, mock_repo, sample_user_id, sample_notification_id):
        mock_repo.get_notification_by_id = AsyncMock(return_value=None)
        with pytest.raises(NotificationNotFoundException):
            await service.get_notification(sample_user_id, sample_notification_id)

    @pytest.mark.asyncio
    async def test_raises_access_denied(self, service, mock_repo, sample_user_id, sample_notification_id):
        other_user_id = uuid4()
        mock_notification = MagicMock(user_id=other_user_id, id=sample_notification_id)
        mock_repo.get_notification_by_id = AsyncMock(return_value=mock_notification)
        with pytest.raises(NotificationAccessDeniedException):
            await service.get_notification(sample_user_id, sample_notification_id)

    @pytest.mark.asyncio
    async def test_returns_notification(self, service, mock_repo, sample_user_id, sample_notification_id):
        mock_notification = MagicMock(user_id=sample_user_id, id=sample_notification_id)
        mock_repo.get_notification_by_id = AsyncMock(return_value=mock_notification)
        result = await service.get_notification(sample_user_id, sample_notification_id)
        assert result == mock_notification


class TestMarkAsRead:
    @pytest.mark.asyncio
    async def test_marks_as_read(self, service, mock_repo, sample_user_id):
        ids = [uuid4(), uuid4()]
        mock_repo.mark_as_read = AsyncMock()
        await service.mark_as_read(sample_user_id, ids)
        mock_repo.mark_as_read.assert_called_once_with(sample_user_id, ids)


class TestGetUnreadCount:
    @pytest.mark.asyncio
    async def test_returns_count(self, service, mock_repo, sample_user_id):
        mock_repo.get_unread_count = AsyncMock(return_value=5)
        count = await service.get_unread_count(sample_user_id)
        assert count == 5
