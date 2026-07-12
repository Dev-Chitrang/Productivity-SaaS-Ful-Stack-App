from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import NotificationSubscription, Notification
from app.modules.notifications.repository import NotificationRepository
from app.modules.notifications.enums import NotificationType
from app.modules.notifications.schemas import PushSubscriptionCreate
from app.modules.notifications.exceptions import (
    NotificationNotFoundException,
    NotificationAccessDeniedException,
)


class NotificationService:
    def __init__(self, repo: NotificationRepository):
        self.repo = repo

    async def register_subscription(self, user_id: UUID, payload: PushSubscriptionCreate) -> NotificationSubscription:
        data = payload.model_dump()
        return await self.repo.create_subscription(user_id, data)

    async def remove_subscription(self, endpoint: str) -> bool:
        return await self.repo.delete_subscription(endpoint)

    async def get_user_notifications(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        notif_type: Optional[NotificationType] = None,
    ) -> tuple[List[Notification], int]:
        return await self.repo.get_user_notifications(user_id, page, page_size, search, notif_type)

    async def get_notification(self, user_id: UUID, notification_id: UUID) -> Notification:
        notification = await self.repo.get_notification_by_id(notification_id)
        if not notification:
            raise NotificationNotFoundException(notification_id)
        if notification.user_id != user_id:
            raise NotificationAccessDeniedException(notification_id, user_id)
        return notification

    async def mark_as_read(self, user_id: UUID, notification_ids: list[UUID]) -> None:
        await self.repo.mark_as_read(user_id, notification_ids)

    async def mark_all_as_read(self, user_id: UUID) -> None:
        await self.repo.mark_all_as_read(user_id)

    async def get_unread_count(self, user_id: UUID) -> int:
        return await self.repo.get_unread_count(user_id)

    async def get_recent_notifications(self, user_id: UUID, limit: int = 5) -> List[Notification]:
        return await self.repo.get_recent_notifications(user_id, limit)
