from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.modules.calender.dependencies import (
    get_current_user_id,
    get_current_user,
    get_calendar_service,
    get_attachment_service,
)
from app.modules.calender.controller import CalendarController
from app.modules.calender.schema import (
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarEventResponse,
    CalendarOccurrenceResponse,
)
from app.modules.calender.enums import EventType, EventColor
from app.modules.calender.exceptions import EventNotFoundException, EventAccessDeniedException
from app.modules.calender.service import CalendarService
from app.modules.attachments.enums import AttachmentEntityType
from app.modules.attachments.exceptions import (
    AttachmentNotFoundException,
    AttachmentStorageError,
    AttachmentValidationError,
)
from app.modules.attachments.schemas import AttachmentListResponse, AttachmentResponse
from app.modules.attachments.service import AttachmentService
from app.models.user import User

from app.core.rate_limit import RateLimiter

router = APIRouter(prefix="/calendar", tags=["Calendar Operations Management Engine"])


# ------------------------------------------------------------------
# CRUD
# ------------------------------------------------------------------

@router.post(
    "/events",
    status_code=status.HTTP_201_CREATED,
    response_model=CalendarEventResponse,
    dependencies=[Depends(RateLimiter(20, 60, "write_entity"))],
)
async def create_event_endpoint(
    payload: CalendarEventCreate,
    current_user: User = Depends(get_current_user),
    service=Depends(get_calendar_service),
):
    ctrl = CalendarController(service)
    return await ctrl.create_user_event(
        current_user.id, payload, user_timezone=current_user.timezone
    )


@router.get(
    "/analytics",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(60, 60, "general_get"))],
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
    dependencies=[Depends(RateLimiter(60, 60, "general_get"))],
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
    dependencies=[Depends(RateLimiter(20, 60, "write_entity"))],
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
    dependencies=[Depends(RateLimiter(20, 60, "write_entity"))],
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
    dependencies=[Depends(RateLimiter(60, 60, "general_get"))],
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


# ------------------------------------------------------------------
# Calendar Event Attachments
# ------------------------------------------------------------------

async def _verify_event_access(
    event_id: UUID,
    current_user_id: UUID,
    calendar_service: CalendarService,
) -> None:
    """Raise 404/403 if the event does not exist or the user does not own it."""
    try:
        await calendar_service.get_event(current_user_id, event_id)
    except EventNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calendar event '{event_id}' not found.",
        )
    except EventAccessDeniedException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this calendar event.",
        )


@router.post(
    "/events/{event_id}/attachments",
    status_code=status.HTTP_201_CREATED,
    response_model=AttachmentResponse,
    summary="Upload an attachment to a calendar event",
    dependencies=[Depends(RateLimiter(3, 60, "file_upload"))],
)
async def upload_calendar_attachment(
    event_id: UUID,
    file: UploadFile = File(...),
    current_user_id: UUID = Depends(get_current_user_id),
    calendar_service: CalendarService = Depends(get_calendar_service),
    attachment_service: AttachmentService = Depends(get_attachment_service),
):
    await _verify_event_access(event_id, current_user_id, calendar_service)
    try:
        attachment = await attachment_service.upload(
            owner_user_id=current_user_id,
            entity_type=AttachmentEntityType.CALENDAR_EVENT,
            entity_id=event_id,
            file=file,
        )
        return AttachmentResponse.model_validate(attachment)
    except AttachmentValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except AttachmentStorageError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get(
    "/events/{event_id}/attachments",
    status_code=status.HTTP_200_OK,
    response_model=AttachmentListResponse,
    summary="List all attachments for a calendar event",
    dependencies=[Depends(RateLimiter(60, 60, "general_get"))],
)
async def list_calendar_attachments(
    event_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    calendar_service: CalendarService = Depends(get_calendar_service),
    attachment_service: AttachmentService = Depends(get_attachment_service),
):
    await _verify_event_access(event_id, current_user_id, calendar_service)
    attachments = await attachment_service.list_all_for_entity(
        AttachmentEntityType.CALENDAR_EVENT, event_id
    )
    return AttachmentListResponse(
        attachments=[AttachmentResponse.model_validate(a) for a in attachments],
        total_count=len(attachments),
    )


@router.get(
    "/events/{event_id}/attachments/{attachment_id}/download",
    response_class=FileResponse,
    summary="Download a calendar event attachment",
    dependencies=[Depends(RateLimiter(60, 60, "general_get"))],
)
async def download_calendar_attachment(
    event_id: UUID,
    attachment_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    calendar_service: CalendarService = Depends(get_calendar_service),
    attachment_service: AttachmentService = Depends(get_attachment_service),
):
    await _verify_event_access(event_id, current_user_id, calendar_service)
    try:
        attachment = await attachment_service.get_for_download_verified(
            attachment_id, AttachmentEntityType.CALENDAR_EVENT, event_id
        )
        return FileResponse(
            path=attachment.storage_path,
            media_type=attachment.content_type,
            filename=attachment.original_filename,
        )
    except AttachmentNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")


@router.delete(
    "/events/{event_id}/attachments/{attachment_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a calendar event attachment",
    dependencies=[Depends(RateLimiter(20, 60, "write_entity"))],
)
async def delete_calendar_attachment(
    event_id: UUID,
    attachment_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    calendar_service: CalendarService = Depends(get_calendar_service),
    attachment_service: AttachmentService = Depends(get_attachment_service),
):
    await _verify_event_access(event_id, current_user_id, calendar_service)
    try:
        await attachment_service.delete_verified(
            attachment_id, AttachmentEntityType.CALENDAR_EVENT, event_id
        )
        return {"status": "success", "message": "Attachment deleted successfully."}
    except AttachmentNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")
