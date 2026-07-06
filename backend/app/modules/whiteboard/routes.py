from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from app.core.rate_limit import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.meetings.dependencies import get_current_user_id # Reusing auth system dependency context
from app.modules.whiteboard.repository import WhiteboardRepository
from app.modules.whiteboard.service import WhiteboardService
from app.modules.whiteboard.controller import WhiteboardController
from app.modules.whiteboard.schemas import (
    WhiteboardCreate, WhiteboardRename, WhiteboardAutosave,
    WhiteboardResponse, WhiteboardFilters
)

router = APIRouter(prefix="/whiteboards", tags=["Persisted Opaque Canvas Layout Documents"])

async def get_whiteboard_service(db: AsyncSession = Depends(get_db)) -> WhiteboardService:
    repo = WhiteboardRepository(db)
    # Note: If your system has an overall activity manager, pass it here as a second argument
    return WhiteboardService(repo)

@router.post("", status_code=status.HTTP_201_CREATED, response_model=WhiteboardResponse, dependencies=[Depends(RateLimiter(20, 60, "write_entity"))])
async def create_board_endpoint(
    payload: WhiteboardCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    service: WhiteboardService = Depends(get_whiteboard_service)
):
    ctrl = WhiteboardController(service)
    return await ctrl.create_board(current_user_id, payload)

@router.get("", status_code=status.HTTP_200_OK, response_model=List[WhiteboardResponse], dependencies=[Depends(RateLimiter(60, 60, "general_get"))])
async def list_boards_endpoint(
    is_archived: bool = Query(False),
    is_deleted: bool = Query(False),
    is_favorite: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    current_user_id: UUID = Depends(get_current_user_id),
    service: WhiteboardService = Depends(get_whiteboard_service)
):
    filters = WhiteboardFilters(
        is_archived=is_archived,
        is_deleted=is_deleted,
        is_favorite=is_favorite,
        search=search
    )
    ctrl = WhiteboardController(service)
    return await ctrl.list_boards(current_user_id, filters)

@router.get("/{id}", status_code=status.HTTP_200_OK, response_model=WhiteboardResponse, dependencies=[Depends(RateLimiter(60, 60, "general_get"))])
async def get_board_endpoint(
    id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: WhiteboardService = Depends(get_whiteboard_service)
):
    ctrl = WhiteboardController(service)
    return await ctrl.get_board(current_user_id, id)

@router.patch("/{id}", status_code=status.HTTP_200_OK, response_model=WhiteboardResponse, dependencies=[Depends(RateLimiter(20, 60, "write_entity"))])
async def rename_board_endpoint(
    id: UUID,
    payload: WhiteboardRename,
    current_user_id: UUID = Depends(get_current_user_id),
    service: WhiteboardService = Depends(get_whiteboard_service)
):
    ctrl = WhiteboardController(service)
    return await ctrl.rename_board(current_user_id, id, payload)

@router.patch("/{id}/board", status_code=status.HTTP_200_OK, response_model=WhiteboardResponse, dependencies=[Depends(RateLimiter(20, 60, "write_entity"))])
async def autosave_board_endpoint(
    id: UUID,
    payload: WhiteboardAutosave,
    current_user_id: UUID = Depends(get_current_user_id),
    service: WhiteboardService = Depends(get_whiteboard_service)
):
    ctrl = WhiteboardController(service)
    return await ctrl.autosave_board(current_user_id, id, payload)

@router.patch("/{id}/favorite", status_code=status.HTTP_200_OK, response_model=WhiteboardResponse, dependencies=[Depends(RateLimiter(20, 60, "write_entity"))])
async def toggle_favorite_endpoint(
    id: UUID,
    is_favorite: bool = Query(...),
    current_user_id: UUID = Depends(get_current_user_id),
    service: WhiteboardService = Depends(get_whiteboard_service)
):
    ctrl = WhiteboardController(service)
    return await ctrl.set_favorite_status(current_user_id, id, is_favorite)

@router.patch("/{id}/archive", status_code=status.HTTP_200_OK, response_model=WhiteboardResponse, dependencies=[Depends(RateLimiter(20, 60, "write_entity"))])
async def toggle_archive_endpoint(
    id: UUID,
    is_archived: bool = Query(...),
    current_user_id: UUID = Depends(get_current_user_id),
    service: WhiteboardService = Depends(get_whiteboard_service)
):
    ctrl = WhiteboardController(service)
    return await ctrl.set_archive_status(current_user_id, id, is_archived)

@router.delete("/{id}", status_code=status.HTTP_200_OK, dependencies=[Depends(RateLimiter(20, 60, "write_entity"))])
async def soft_delete_board_endpoint(
    id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: WhiteboardService = Depends(get_whiteboard_service)
):
    ctrl = WhiteboardController(service)
    return await ctrl.delete_board(current_user_id, id)

@router.patch("/{id}/restore", status_code=status.HTTP_200_OK, response_model=WhiteboardResponse, dependencies=[Depends(RateLimiter(20, 60, "write_entity"))])
async def restore_board_endpoint(
    id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: WhiteboardService = Depends(get_whiteboard_service)
):
    ctrl = WhiteboardController(service)
    return await ctrl.restore_board(current_user_id, id)
