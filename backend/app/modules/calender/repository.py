from datetime import datetime, timezone, timedelta
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, asc, func

from app.models.calender import CalendarEvent
from app.modules.calender.enums import EventType, EventColor


class CalendarRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create(self, user_id: UUID, event_data: dict) -> CalendarEvent:
        try:
            event = CalendarEvent(user_id=user_id, **event_data)
            self.db.add(event)
            await self.db.flush()
            return event
        except Exception:
            await self.db.rollback()
            raise

    async def get_by_id(self, event_id: UUID) -> Optional[CalendarEvent]:
        stmt = select(CalendarEvent).where(
            and_(
                CalendarEvent.id == event_id,
                CalendarEvent.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, event: CalendarEvent, update_data: dict) -> CalendarEvent:
        try:
            for key, value in update_data.items():
                setattr(event, key, value)
            self.db.add(event)
            await self.db.flush()
            return event
        except Exception:
            await self.db.rollback()
            raise

    async def soft_delete(self, event: CalendarEvent) -> None:
        try:
            event.deleted_at = datetime.utcnow()
            self.db.add(event)
            await self.db.flush()
        except Exception:
            await self.db.rollback()
            raise

    # ------------------------------------------------------------------
    # Listing / querying
    # ------------------------------------------------------------------

    async def get_analytics(self, user_id: UUID) -> dict:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        total = await self.db.scalar(
            select(func.count(CalendarEvent.id)).where(and_(CalendarEvent.user_id == user_id, CalendarEvent.deleted_at.is_(None)))
        )
        today_count = await self.db.scalar(
            select(func.count(CalendarEvent.id)).where(
                and_(
                    CalendarEvent.user_id == user_id,
                    CalendarEvent.deleted_at.is_(None),
                    CalendarEvent.start_time < today_end,
                    CalendarEvent.end_time > today_start,
                )
            )
        )
        upcoming = await self.db.scalar(
            select(func.count(CalendarEvent.id)).where(
                and_(CalendarEvent.user_id == user_id, CalendarEvent.deleted_at.is_(None), CalendarEvent.start_time >= today_end)
            )
        )

        six_months_ago = now - timedelta(days=180)
        month_expr = func.date_trunc("month", CalendarEvent.start_time).label("month")
        monthly_rows = await self.db.execute(
            select(
                month_expr,
                func.count(CalendarEvent.id).label("count"),
            )
            .where(
                and_(
                    CalendarEvent.user_id == user_id,
                    CalendarEvent.deleted_at.is_(None),
                    CalendarEvent.start_time >= six_months_ago,
                )
            )
            .group_by(month_expr)
            .order_by(month_expr)
        )
        monthly_data = [{"month": row.month.isoformat(), "count": row.count} for row in monthly_rows]

        past = await self.db.scalar(
            select(func.count(CalendarEvent.id)).where(
                and_(CalendarEvent.user_id == user_id, CalendarEvent.deleted_at.is_(None), CalendarEvent.end_time < now)
            )
        )
        future = await self.db.scalar(
            select(func.count(CalendarEvent.id)).where(
                and_(CalendarEvent.user_id == user_id, CalendarEvent.deleted_at.is_(None), CalendarEvent.start_time >= now)
            )
        )

        next_events_stmt = (
            select(CalendarEvent)
            .where(
                and_(
                    CalendarEvent.user_id == user_id,
                    CalendarEvent.deleted_at.is_(None),
                    CalendarEvent.start_time >= now,
                )
            )
            .order_by(asc(CalendarEvent.start_time))
            .limit(3)
        )
        next_events_result = await self.db.execute(next_events_stmt)
        next_events = [
            {
                "id": str(e.id),
                "title": e.title,
                "start_time": e.start_time.isoformat(),
                "end_time": e.end_time.isoformat(),
                "color": e.color.value if e.color else None,
            }
            for e in next_events_result.scalars().all()
        ]

        return {
            "total": total or 0,
            "today": today_count or 0,
            "upcoming": upcoming or 0,
            "monthly_events": monthly_data,
            "past_events": past or 0,
            "future_events": future or 0,
            "next_events": next_events,
        }

    async def list_events(
        self,
        user_id: UUID,
        range_start: datetime,
        range_end: datetime,
        search_query: Optional[str] = None,
        event_type: Optional[EventType] = None,
        color: Optional[EventColor] = None,
    ) -> Sequence[CalendarEvent]:
        """
        Returns all non-deleted events belonging to `user_id` whose time window
        overlaps with [range_start, range_end].

        Overlap condition:  event.start_time < range_end
                        AND event.end_time   > range_start

        This correctly captures events that:
          - start before the window and end inside it
          - start inside the window and end after it
          - span the entire window
          - are fully contained within the window

        Optional keyword filters are applied additively.
        The caller (service) is responsible for recurring-event expansion.
        """
        conditions = [
            CalendarEvent.user_id == user_id,
            CalendarEvent.deleted_at.is_(None),
            CalendarEvent.start_time < range_end,
            CalendarEvent.end_time > range_start,
        ]

        if search_query:
            conditions.append(
                or_(
                    CalendarEvent.title.ilike(f"%{search_query}%"),
                    CalendarEvent.description.ilike(f"%{search_query}%"),
                )
            )

        if event_type:
            conditions.append(CalendarEvent.event_type == event_type)

        if color:
            conditions.append(CalendarEvent.color == color)

        stmt = (
            select(CalendarEvent)
            .where(and_(*conditions))
            .order_by(asc(CalendarEvent.start_time))
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
