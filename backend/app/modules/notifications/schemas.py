from uuid import UUID
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field

from app.modules.notifications.enums import NotificationType


class PushSubscriptionCreate(BaseModel):
    endpoint: str = Field(..., max_length=512)
    p256dh: str = Field(..., max_length=256)
    auth: str = Field(..., max_length=256)
    browser: Optional[str] = Field(None, max_length=50)


class PushSubscriptionResponse(BaseModel):
    id: UUID
    user_id: UUID
    endpoint: str
    browser: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    type: NotificationType
    title: str
    body: str
    extra_data: Optional[dict[str, Any]] = None
    is_read: bool
    sent_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    page_size: int


class NotificationMarkReadRequest(BaseModel):
    notification_ids: list[UUID]


class NotificationUnreadCountResponse(BaseModel):
    count: int
