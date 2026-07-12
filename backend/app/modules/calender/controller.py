from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import HTTPException, status

from app.modules.calender.service import CalendarService
from app.modules.calender.schema import (
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarEventResponse,
    CalendarOccurrenceResponse,
)
from app.modules.calender.enums import EventType, EventColor
from app.modules.calender.exceptions import (
    EventNotFoundException,
    EventAccessDeniedException,
    CalendarValidationError,
)


class CalendarController:
    def __init__(self, service: CalendarService):
        self.service = service

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create_user_event(
        self, user_id: UUID, payload: CalendarEventCreate, user_timezone: Optional[str] = None
    ) -> CalendarEventResponse:
        try:
            event = await self.service.create_event(user_id, payload, user_timezone=user_timezone)
            return CalendarEventResponse.model_validate(event)
        except CalendarValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_user_event(self, user_id: UUID, event_id: UUID) -> CalendarEventResponse:
        try:
            event = await self.service.get_event(user_id, event_id)
            return CalendarEventResponse.model_validate(event)
        except EventNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except EventAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def update_user_event(
        self, user_id: UUID, event_id: UUID, payload: CalendarEventUpdate
    ) -> CalendarEventResponse:
        try:
            event = await self.service.update_event(user_id, event_id, payload)
            return CalendarEventResponse.model_validate(event)
        except EventNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except EventAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except CalendarValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def delete_user_event(self, user_id: UUID, event_id: UUID) -> dict:
        try:
            await self.service.delete_event(user_id, event_id)
            return {"status": "success", "message": "Calendar event successfully soft deleted."}
        except EventNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except EventAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    async def get_analytics(self, user_id: UUID) -> dict:
        return await self.service.get_analytics(user_id)

    async def list_user_events(
        self,
        user_id: UUID,
        range_start: datetime,
        range_end: datetime,
        search: Optional[str],
        event_type: Optional[EventType],
        color: Optional[EventColor],
    ) -> List[CalendarOccurrenceResponse]:
        try:
            return await self.service.list_events(
                user_id=user_id,
                range_start=range_start,
                range_end=range_end,
                search_query=search,
                event_type=event_type,
                color=color,
            )
        except CalendarValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
