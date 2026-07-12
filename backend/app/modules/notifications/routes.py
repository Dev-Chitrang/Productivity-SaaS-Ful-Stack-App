from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import RateLimiter
from app.modules.meetings.dependencies import get_current_user_id
from app.modules.notifications.repository import NotificationRepository
from app.modules.notifications.service import NotificationService
from app.modules.notifications.controller import NotificationController
from app.modules.notifications.enums import NotificationType
from app.modules.notifications.schemas import (
    PushSubscriptionCreate,
    PushSubscriptionResponse,
    NotificationResponse,
    NotificationListResponse,
    NotificationMarkReadRequest,
    NotificationUnreadCountResponse,
)

router = APIRouter(prefix="/notifications", tags=["Notification Center"])


def _get_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(NotificationRepository(db))


@router.post(
    "/subscriptions",
    status_code=status.HTTP_201_CREATED,
    response_model=PushSubscriptionResponse,
    dependencies=[Depends(RateLimiter(10, 60, "notification_subscription"))],
)
async def register_push_subscription_endpoint(
    payload: PushSubscriptionCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(_get_service),
):
    ctrl = NotificationController(service)
    return await ctrl.register_subscription(current_user_id, payload)


@router.delete(
    "/subscriptions",
    dependencies=[Depends(RateLimiter(20, 60, "notification_subscription_delete"))],
)
async def remove_push_subscription_endpoint(
    endpoint: str = Query(...),
    current_user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(_get_service),
):
    ctrl = NotificationController(service)
    return await ctrl.remove_subscription(endpoint)


@router.get("", response_model=NotificationListResponse)
async def list_notifications_endpoint(
    current_user_id: UUID = Depends(get_current_user_id),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, max_length=200),
    type: Optional[NotificationType] = Query(None),
    service: NotificationService = Depends(_get_service),
):
    ctrl = NotificationController(service)
    return await ctrl.list_notifications(current_user_id, page, page_size, search, type)


@router.get("/unread-count", response_model=NotificationUnreadCountResponse)
async def get_unread_count_endpoint(
    current_user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(_get_service),
):
    ctrl = NotificationController(service)
    return await ctrl.get_unread_count(current_user_id)


@router.get("/recent")
async def get_recent_notifications_endpoint(
    current_user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(_get_service),
):
    ctrl = NotificationController(service)
    return await ctrl.get_recent(current_user_id)


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification_endpoint(
    notification_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(_get_service),
):
    ctrl = NotificationController(service)
    return await ctrl.get_notification(current_user_id, notification_id)


@router.post("/mark-read")
async def mark_as_read_endpoint(
    payload: NotificationMarkReadRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(_get_service),
):
    ctrl = NotificationController(service)
    return await ctrl.mark_as_read(current_user_id, payload.notification_ids)


@router.post("/mark-all-read")
async def mark_all_as_read_endpoint(
    current_user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(_get_service),
):
    ctrl = NotificationController(service)
    return await ctrl.mark_all_as_read(current_user_id)
