from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from app.modules.calender.repository import CalendarRepository
from app.models.calender import CalendarEvent
from app.modules.calender.schema import CalendarEventCreate, CalendarEventUpdate, CalendarOccurrenceResponse
from app.modules.calender.enums import EventType, EventColor
from app.modules.calender.recurrence import RecurrenceEngine
from app.modules.calender.exceptions import (
    EventNotFoundException,
    EventAccessDeniedException,
    CalendarValidationError,
)


class CalendarService:
    def __init__(self, repo: CalendarRepository, attachment_service=None):
        self.repo = repo
        self._attachment_service = attachment_service

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create_event(self, user_id: UUID, payload: CalendarEventCreate) -> CalendarEvent:
        now = datetime.now(timezone.utc)
        if payload.start_time < now:
            raise CalendarValidationError(
                "Cannot create an event in the past. Start time must be in the future."
            )
        if payload.start_time >= payload.end_time:
            raise CalendarValidationError(
                "Event start time must be before end time."
            )
        return await self.repo.create(user_id, payload.model_dump())

    async def get_event(self, user_id: UUID, event_id: UUID) -> CalendarEvent:
        event = await self.repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(event_id)
        if event.user_id != user_id:
            raise EventAccessDeniedException(event_id, user_id)
        return event

    async def update_event(
        self, user_id: UUID, event_id: UUID, payload: CalendarEventUpdate
    ) -> CalendarEvent:
        event = await self.get_event(user_id, event_id)
        update_dict = payload.model_dump(exclude_unset=True)

        now = datetime.now(timezone.utc)
        updated_start = update_dict.get("start_time", event.start_time)
        updated_end = update_dict.get("end_time", event.end_time)

        if "start_time" in update_dict and updated_start < now:
            raise CalendarValidationError(
                "Cannot move an event to the past. Start time must be in the future."
            )

        if updated_start >= updated_end:
            raise CalendarValidationError(
                "Event start time must be before end time."
            )

        updated_rec_end = update_dict.get("recurrence_end_date", event.recurrence_end_date)
        if updated_rec_end and updated_rec_end < updated_start:
            raise CalendarValidationError(
                "Recurrence end date cannot terminate prior to the series start time."
            )

        return await self.repo.update(event, update_dict)

    async def delete_event(self, user_id: UUID, event_id: UUID) -> None:
        event = await self.get_event(user_id, event_id)
        # Cascade: remove all attachments before soft-deleting the event
        if self._attachment_service is not None:
            from app.modules.attachments.enums import AttachmentEntityType
            await self._attachment_service.delete_all_for_entity(
                AttachmentEntityType.CALENDAR_EVENT, event_id
            )
        await self.repo.soft_delete(event)

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    async def get_analytics(self, user_id: UUID) -> dict:
        return await self.repo.get_analytics(user_id)

    async def list_events(
        self,
        user_id: UUID,
        range_start: datetime,
        range_end: datetime,
        search_query: Optional[str] = None,
        event_type: Optional[EventType] = None,
        color: Optional[EventColor] = None,
    ) -> List[CalendarOccurrenceResponse]:
        """
        Returns all events (including expanded recurring occurrences) for the
        authenticated user that fall within [range_start, range_end].

        Responsibilities:
          - Validates that range_start < range_end.
          - Delegates the DB query to the repository.
          - Expands recurring events via RecurrenceEngine (only within the
            requested window — no occurrences outside are ever generated).
          - Returns a flat, chronologically sorted list ready for the client
            to render in whichever view it chooses.
        """
        if range_start >= range_end:
            raise CalendarValidationError(
                "range_start must be chronologically before range_end."
            )

        raw_events = await self.repo.list_events(
            user_id=user_id,
            range_start=range_start,
            range_end=range_end,
            search_query=search_query,
            event_type=event_type,
            color=color,
        )

        occurrences: List[CalendarOccurrenceResponse] = []

        for event in raw_events:
            if event.recurrence_frequency is not None:
                # Expand the series — only occurrences inside the window are returned
                expanded = RecurrenceEngine.generate_occurrences_for_event(
                    event, range_start, range_end
                )
                occurrences.extend(expanded)
            else:
                # Non-recurring: pass through directly as a single occurrence
                occurrences.append(
                    CalendarOccurrenceResponse(
                        id=event.id,
                        title=event.title,
                        description=event.description,
                        event_type=event.event_type,
                        color=event.color,
                        start_time=event.start_time,
                        end_time=event.end_time,
                        timezone=event.timezone,
                        is_all_day=event.is_all_day,
                        location=event.location,
                        is_recurring=False,
                    )
                )

        occurrences.sort(key=lambda o: o.start_time)
        return occurrences
