from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query

from app.modules.notes.dependencies import get_current_user_id, get_notes_service
from app.modules.notes.controller import NoteController
from app.modules.notes.schemas import NoteCreate, NoteUpdate, NoteResponse, NoteListResponse

router = APIRouter(prefix="/notes", tags=["Knowledge & Notes Management Engine"])

@router.post("", status_code=status.HTTP_201_CREATED, response_model=NoteResponse)
async def create_note_endpoint(
    payload: NoteCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_notes_service)
):
    ctrl = NoteController(service)
    return await ctrl.create_user_note(current_user_id, payload)

@router.get("", status_code=status.HTTP_200_OK, response_model=NoteListResponse)
async def list_notes_endpoint(
    search: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    favorite: Optional[bool] = None,
    pinned: Optional[bool] = None,
    archived: Optional[bool] = False,
    deleted: bool = False,
    sort_by: str = Query("updated_at", enum=["updated_at", "created_at", "title"]),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_notes_service)
):
    ctrl = NoteController(service)
    return await ctrl.list_user_notes(
        current_user_id, search, category, tag, favorite, pinned, archived, deleted, sort_by, sort_order
    )

@router.get("/{note_id}", status_code=status.HTTP_200_OK, response_model=NoteResponse)
async def get_note_endpoint(
    note_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_notes_service)
):
    ctrl = NoteController(service)
    return await ctrl.get_user_note(current_user_id, note_id)

@router.patch("/{note_id}", status_code=status.HTTP_200_OK, response_model=NoteResponse)
async def update_note_endpoint(
    note_id: UUID,
    payload: NoteUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_notes_service)
):
    ctrl = NoteController(service)
    return await ctrl.update_user_note(current_user_id, note_id, payload)

@router.delete("/{note_id}", status_code=status.HTTP_200_OK)
async def delete_note_endpoint(
    note_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_notes_service)
):
    ctrl = NoteController(service)
    return await ctrl.delete_user_note(current_user_id, note_id)

@router.patch("/{note_id}/restore", status_code=status.HTTP_200_OK, response_model=NoteResponse)
async def restore_note_endpoint(
    note_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_notes_service)
):
    ctrl = NoteController(service)
    return await ctrl.restore_user_note(current_user_id, note_id)

@router.patch("/{note_id}/archive", status_code=status.HTTP_200_OK, response_model=NoteResponse)
async def archive_note_endpoint(
    note_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_notes_service)
):
    ctrl = NoteController(service)
    return await ctrl.archive_user_note(current_user_id, note_id)

@router.patch("/{note_id}/unarchive", status_code=status.HTTP_200_OK, response_model=NoteResponse)
async def unarchive_note_endpoint(
    note_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_notes_service)
):
    ctrl = NoteController(service)
    return await ctrl.unarchive_user_note(current_user_id, note_id)

@router.patch("/{note_id}/pin", status_code=status.HTTP_200_OK, response_model=NoteResponse)
async def pin_note_endpoint(
    note_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_notes_service)
):
    ctrl = NoteController(service)
    return await ctrl.pin_user_note(current_user_id, note_id)

@router.patch("/{note_id}/unpin", status_code=status.HTTP_200_OK, response_model=NoteResponse)
async def unpin_note_endpoint(
    note_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_notes_service)
):
    ctrl = NoteController(service)
    return await ctrl.unpin_user_note(current_user_id, note_id)

@router.patch("/{note_id}/favorite", status_code=status.HTTP_200_OK, response_model=NoteResponse)
async def favorite_note_endpoint(
    note_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_notes_service)
):
    ctrl = NoteController(service)
    return await ctrl.favorite_user_note(current_user_id, note_id)

@router.patch("/{note_id}/unfavorite", status_code=status.HTTP_200_OK, response_model=NoteResponse)
async def unfavorite_note_endpoint(
    note_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_notes_service)
):
    ctrl = NoteController(service)
    return await ctrl.unfavorite_user_note(current_user_id, note_id)
