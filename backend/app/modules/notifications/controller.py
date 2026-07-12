from uuid import UUID
from typing import Optional
from fastapi import HTTPException, status

from app.modules.notifications.service import NotificationService
from app.modules.notifications.enums import NotificationType
from app.modules.notifications.schemas import (
    PushSubscriptionCreate,
    PushSubscriptionResponse,
    NotificationResponse,
    NotificationListResponse,
    NotificationUnreadCountResponse,
)
from app.modules.notifications.exceptions import (
    NotificationNotFoundException,
    NotificationAccessDeniedException,
)


class NotificationController:
    def __init__(self, service: NotificationService):
        self.service = service

    async def register_subscription(self, user_id: UUID, payload: PushSubscriptionCreate) -> dict:
        subscription = await self.service.register_subscription(user_id, payload)
        return PushSubscriptionResponse.model_validate(subscription)

    async def remove_subscription(self, endpoint: str) -> dict:
        removed = await self.service.remove_subscription(endpoint)
        return {"removed": removed}

    async def list_notifications(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        notif_type: Optional[NotificationType] = None,
    ) -> dict:
        items, total = await self.service.get_user_notifications(user_id, page, page_size, search, notif_type)
        return NotificationListResponse(
            items=[NotificationResponse.model_validate(n) for n in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_notification(self, user_id: UUID, notification_id: UUID) -> dict:
        try:
            notification = await self.service.get_notification(user_id, notification_id)
            return NotificationResponse.model_validate(notification)
        except NotificationNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except NotificationAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def mark_as_read(self, user_id: UUID, notification_ids: list[UUID]) -> dict:
        await self.service.mark_as_read(user_id, notification_ids)
        return {"marked": len(notification_ids)}

    async def mark_all_as_read(self, user_id: UUID) -> dict:
        await self.service.mark_all_as_read(user_id)
        return {"marked": "all"}

    async def get_unread_count(self, user_id: UUID) -> dict:
        count = await self.service.get_unread_count(user_id)
        return NotificationUnreadCountResponse(count=count)

    async def get_recent(self, user_id: UUID) -> dict:
        items = await self.service.get_recent_notifications(user_id)
        return [NotificationResponse.model_validate(n) for n in items]
