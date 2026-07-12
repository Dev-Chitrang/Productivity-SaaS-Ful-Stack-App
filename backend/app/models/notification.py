from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from uuid6 import uuid7
from app.core.database import Base
from app.modules.notifications.enums import NotificationType


class NotificationSubscription(Base):
    __tablename__ = "notification_subscriptions"
    __table_args__ = {"extend_existing": True}

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid7)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    endpoint = Column(String(512), nullable=False)
    p256dh = Column(String(256), nullable=False)
    auth = Column(String(256), nullable=False)
    browser = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_created", "user_id", "created_at"),
        {"extend_existing": True},
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid7)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    type = Column(SQLEnum(NotificationType, name="notification_type_enum"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    body = Column(String(1000), nullable=False)
    extra_data = Column(JSONB, nullable=True)

    is_read = Column(Boolean, nullable=False, default=False, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime(timezone=True), nullable=True)
