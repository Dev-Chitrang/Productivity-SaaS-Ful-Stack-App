from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.modules.calender.dependencies import get_current_user_id, get_calendar_service
from app.modules.calender.controller import CalendarController
from app.modules.calender.schema import (
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarEventResponse,
    CalendarOccurrenceResponse,
)
from app.modules.calender.enums import EventType, EventColor

router = APIRouter(prefix="/calendar", tags=["Calendar Operations Management Engine"])


# ------------------------------------------------------------------
# CRUD
# ------------------------------------------------------------------

@router.post(
    "/events",
    status_code=status.HTTP_201_CREATED,
    response_model=CalendarEventResponse,
)
async def create_event_endpoint(
    payload: CalendarEventCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    service=Depends(get_calendar_service),
):
    ctrl = CalendarController(service)
    return await ctrl.create_user_event(current_user_id, payload)


@router.get(
    "/analytics",
    status_code=status.HTTP_200_OK,
)
async def calendar_analytics_endpoint(
    current_user_id: UUID = Depends(get_current_user_id),
    service=Depends(get_calendar_service),
):
    ctrl = CalendarController(service)
    return await ctrl.get_analytics(current_user_id)


@router.get(
    "/events/{event_id}",
    status_code=status.HTTP_200_OK,
    response_model=CalendarEventResponse,
)
async def get_event_endpoint(
    event_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service=Depends(get_calendar_service),
):
    ctrl = CalendarController(service)
    return await ctrl.get_user_event(current_user_id, event_id)


@router.patch(
    "/events/{event_id}",
    status_code=status.HTTP_200_OK,
    response_model=CalendarEventResponse,
)
async def update_event_endpoint(
    event_id: UUID,
    payload: CalendarEventUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    service=Depends(get_calendar_service),
):
    ctrl = CalendarController(service)
    return await ctrl.update_user_event(current_user_id, event_id, payload)


@router.delete(
    "/events/{event_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_event_endpoint(
    event_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service=Depends(get_calendar_service),
):
    ctrl = CalendarController(service)
    return await ctrl.delete_user_event(current_user_id, event_id)


# ------------------------------------------------------------------
# Listing — single endpoint consumed by all calendar views
# ------------------------------------------------------------------

@router.get(
    "/events",
    status_code=status.HTTP_200_OK,
    response_model=List[CalendarOccurrenceResponse],
    summary="List calendar events within a date range",
    description=(
        "Returns every event (including expanded recurring occurrences) belonging to the "
        "authenticated user that overlaps the requested [start, end] window. "
        "The frontend is responsible for rendering the returned events in whichever "
        "view layout it chooses (month grid, week grid, day timeline, agenda list, etc.)."
    ),
)
async def list_events_endpoint(
    start: datetime = Query(..., description="Range start — inclusive, ISO 8601 with timezone."),
    end: datetime = Query(..., description="Range end — inclusive, ISO 8601 with timezone."),
    search: Optional[str] = Query(None, description="Full-text search against title and description."),
    event_type: Optional[EventType] = Query(None, description="Filter by event type enum value."),
    color: Optional[EventColor] = Query(None, description="Filter by event color enum value."),
    current_user_id: UUID = Depends(get_current_user_id),
    service=Depends(get_calendar_service),
):
    ctrl = CalendarController(service)
    return await ctrl.list_user_events(
        user_id=current_user_id,
        range_start=start,
        range_end=end,
        search=search,
        event_type=event_type,
        color=color,
    )
