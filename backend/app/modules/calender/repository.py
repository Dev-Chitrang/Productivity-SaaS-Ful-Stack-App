from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, asc

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
