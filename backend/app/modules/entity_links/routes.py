from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.modules.entity_links.controller import EntityLinkController
from app.modules.entity_links.dependencies import get_current_user_id, get_entity_link_service
from app.modules.entity_links.schemas import (
    EntityLinkCreate,
    EntityLinkListResponse,
    EntityLinkResponse,
    LinkedTaskResponse,
    LinkedMeetingResponse,
)
from app.modules.entity_links.services import EntityLinkService

router = APIRouter(prefix="/entity-links", tags=["Entity Links"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=EntityLinkResponse)
async def create_link_endpoint(
    payload: EntityLinkCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    service: EntityLinkService = Depends(get_entity_link_service),
):
    ctrl = EntityLinkController(service)
    return await ctrl.create_link(current_user_id, payload)


@router.delete("/{link_id}", status_code=status.HTTP_200_OK)
async def delete_link_endpoint(
    link_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: EntityLinkService = Depends(get_entity_link_service),
):
    ctrl = EntityLinkController(service)
    return await ctrl.delete_link(current_user_id, link_id)


@router.get("", status_code=status.HTTP_200_OK, response_model=EntityLinkListResponse)
async def list_links_endpoint(
    source_type: Optional[str] = Query(None),
    source_id: Optional[UUID] = Query(None),
    target_type: Optional[str] = Query(None),
    target_id: Optional[UUID] = Query(None),
    current_user_id: UUID = Depends(get_current_user_id),
    service: EntityLinkService = Depends(get_entity_link_service),
):
    ctrl = EntityLinkController(service)
    return await ctrl.list_links(
        current_user_id,
        source_type=source_type,
        source_id=source_id,
        target_type=target_type,
        target_id=target_id,
    )


linked_tasks_router = APIRouter(prefix="/meetings", tags=["Meeting Linked Tasks"])


@linked_tasks_router.get(
    "/{meeting_id}/linked-tasks",
    status_code=status.HTTP_200_OK,
    response_model=List[LinkedTaskResponse],
)
async def get_linked_tasks_endpoint(
    meeting_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: EntityLinkService = Depends(get_entity_link_service),
):
    ctrl = EntityLinkController(service)
    return await ctrl.get_linked_tasks(current_user_id, meeting_id)


linked_session_tasks_router = APIRouter(prefix="/meetings", tags=["Session Linked Tasks"])


@linked_session_tasks_router.get(
    "/{meeting_id}/sessions/{session_id}/linked-tasks",
    status_code=status.HTTP_200_OK,
    response_model=List[LinkedTaskResponse],
)
async def get_session_linked_tasks_endpoint(
    meeting_id: UUID,
    session_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: EntityLinkService = Depends(get_entity_link_service),
):
    ctrl = EntityLinkController(service)
    return await ctrl.get_linked_tasks_for_session(current_user_id, session_id)


linked_meetings_router = APIRouter(prefix="/tasks", tags=["Task Linked Meetings"])


@linked_meetings_router.get(
    "/{task_id}/linked-meetings",
    status_code=status.HTTP_200_OK,
    response_model=List[LinkedMeetingResponse],
)
async def get_linked_meetings_endpoint(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: EntityLinkService = Depends(get_entity_link_service),
):
    ctrl = EntityLinkController(service)
    return await ctrl.get_linked_meetings(current_user_id, task_id)
