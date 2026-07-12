from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, and_, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import NotificationSubscription, Notification
from app.modules.notifications.enums import NotificationType


class NotificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_subscription(self, user_id: UUID, data: dict) -> NotificationSubscription:
        existing = await self.get_subscription_by_endpoint(data["endpoint"])
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            existing.updated_at = datetime.now(timezone.utc)
            self.db.add(existing)
            await self.db.flush()
            return existing

        subscription = NotificationSubscription(user_id=user_id, **data)
        self.db.add(subscription)
        await self.db.flush()
        return subscription

    async def get_subscription_by_endpoint(self, endpoint: str) -> Optional[NotificationSubscription]:
        stmt = select(NotificationSubscription).where(
            and_(
                NotificationSubscription.endpoint == endpoint,
                NotificationSubscription.deleted_at.is_(None),
            )
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_active_subscriptions_by_user(self, user_id: UUID) -> List[NotificationSubscription]:
        stmt = select(NotificationSubscription).where(
            and_(
                NotificationSubscription.user_id == user_id,
                NotificationSubscription.deleted_at.is_(None),
            )
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def delete_subscription(self, endpoint: str) -> bool:
        subscription = await self.get_subscription_by_endpoint(endpoint)
        if not subscription:
            return False
        subscription.deleted_at = datetime.now(timezone.utc)
        self.db.add(subscription)
        await self.db.flush()
        return True

    async def create_notification(self, user_id: UUID, notif_type: NotificationType, title: str, body: str, extra_data: Optional[dict] = None) -> Notification:
        notification = Notification(
            user_id=user_id,
            type=notif_type,
            title=title,
            body=body,
            extra_data=extra_data,
            sent_at=datetime.now(timezone.utc),
        )
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def get_notification_by_id(self, notification_id: UUID) -> Optional[Notification]:
        stmt = select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.deleted_at.is_(None),
            )
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_user_notifications(self, user_id: UUID, page: int = 1, page_size: int = 20, search: Optional[str] = None, notif_type: Optional[NotificationType] = None) -> tuple[List[Notification], int]:
        base_filter = and_(
            Notification.user_id == user_id,
            Notification.deleted_at.is_(None),
        )

        count_stmt = select(func.count(Notification.id)).where(base_filter)
        query_stmt = select(Notification).where(base_filter)

        if search:
            search_filter = or_(
                Notification.title.ilike(f"%{search}%"),
                Notification.body.ilike(f"%{search}%"),
            )
            count_stmt = count_stmt.where(search_filter)
            query_stmt = query_stmt.where(search_filter)

        if notif_type:
            type_filter = Notification.type == notif_type
            count_stmt = count_stmt.where(type_filter)
            query_stmt = query_stmt.where(type_filter)

        total = (await self.db.execute(count_stmt)).scalar() or 0

        query_stmt = query_stmt.order_by(Notification.created_at.desc())
        query_stmt = query_stmt.offset((page - 1) * page_size).limit(page_size)

        items = list((await self.db.execute(query_stmt)).scalars().all())
        return items, total

    async def mark_as_read(self, user_id: UUID, notification_ids: List[UUID]) -> None:
        stmt = (
            update(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.id.in_(notification_ids),
                    Notification.is_read == False,
                    Notification.deleted_at.is_(None),
                )
            )
            .values(is_read=True)
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def mark_all_as_read(self, user_id: UUID) -> None:
        stmt = (
            update(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False,
                    Notification.deleted_at.is_(None),
                )
            )
            .values(is_read=True)
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def get_unread_count(self, user_id: UUID) -> int:
        stmt = select(func.count(Notification.id)).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False,
                Notification.deleted_at.is_(None),
            )
        )
        return (await self.db.execute(stmt)).scalar() or 0

    async def get_recent_notifications(self, user_id: UUID, limit: int = 5) -> List[Notification]:
        stmt = (
            select(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.deleted_at.is_(None),
                )
            )
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def has_sent_meeting_reminder(self, user_id: UUID, meeting_id: UUID) -> bool:
        stmt = select(func.count(Notification.id)).where(
            and_(
                Notification.user_id == user_id,
                Notification.type == NotificationType.MEETING_REMINDER,
                Notification.extra_data["meeting_id"].as_string() == str(meeting_id),
                Notification.deleted_at.is_(None),
            )
        )
        return (await self.db.execute(stmt)).scalar() > 0


from sqlalchemy import or_
