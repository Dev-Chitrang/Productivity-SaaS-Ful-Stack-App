from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status

from app.modules.notes.services import NoteService
from app.modules.notes.schemas import NoteCreate, NoteUpdate, NoteResponse, NoteListResponse
from app.modules.notes.exceptions import (
    NoteNotFoundException,
    NoteAccessDeniedException,
    NoteValidationError
)

class NoteController:
    def __init__(self, service: NoteService):
        self.service = service

    async def create_user_note(self, user_id: UUID, payload: NoteCreate) -> dict:
        try:
            note = await self.service.create_note(user_id, payload)
            return NoteResponse.model_validate(note)
        except NoteValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_user_note(self, user_id: UUID, note_id: UUID) -> dict:
        try:
            note = await self.service.get_note(user_id, note_id, include_deleted=True)
            return NoteResponse.model_validate(note)
        except NoteNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except NoteAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def update_user_note(self, user_id: UUID, note_id: UUID, payload: NoteUpdate) -> dict:
        try:
            note = await self.service.update_note(user_id, note_id, payload)
            return NoteResponse.model_validate(note)
        except NoteNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except NoteAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except NoteValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def delete_user_note(self, user_id: UUID, note_id: UUID) -> dict:
        try:
            await self.service.delete_note(user_id, note_id)
            return {"status": "success", "message": "Note moved to trash successfully."}
        except NoteNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except NoteAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def restore_user_note(self, user_id: UUID, note_id: UUID) -> dict:
        try:
            note = await self.service.restore_note(user_id, note_id)
            return NoteResponse.model_validate(note)
        except NoteNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except NoteAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except NoteValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def archive_user_note(self, user_id: UUID, note_id: UUID) -> dict:
        try:
            note = await self.service.toggle_archive_status(user_id, note_id, archive=True)
            return NoteResponse.model_validate(note)
        except NoteNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except NoteAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def unarchive_user_note(self, user_id: UUID, note_id: UUID) -> dict:
        try:
            note = await self.service.toggle_archive_status(user_id, note_id, archive=False)
            return NoteResponse.model_validate(note)
        except NoteNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except NoteAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def pin_user_note(self, user_id: UUID, note_id: UUID) -> dict:
        try:
            note = await self.service.toggle_pin_status(user_id, note_id, pin=True)
            return NoteResponse.model_validate(note)
        except NoteNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except NoteAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def unpin_user_note(self, user_id: UUID, note_id: UUID) -> dict:
        try:
            note = await self.service.toggle_pin_status(user_id, note_id, pin=False)
            return NoteResponse.model_validate(note)
        except NoteNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except NoteAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def favorite_user_note(self, user_id: UUID, note_id: UUID) -> dict:
        try:
            note = await self.service.toggle_favorite_status(user_id, note_id, favorite=True)
            return NoteResponse.model_validate(note)
        except NoteNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except NoteAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def unfavorite_user_note(self, user_id: UUID, note_id: UUID) -> dict:
        try:
            note = await self.service.toggle_favorite_status(user_id, note_id, favorite=False)
            return NoteResponse.model_validate(note)
        except NoteNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except NoteAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def list_user_notes(
        self,
        user_id: UUID,
        search: Optional[str],
        category: Optional[str],
        tag: Optional[str],
        favorite: Optional[bool],
        pinned: Optional[bool],
        archived: Optional[bool],
        deleted: bool,
        sort_by: str,
        sort_order: str
    ) -> dict:
        notes = await self.service.list_and_filter_notes(
            user_id=user_id, search=search, category=category, tag=tag,
            favorite=favorite, pinned=pinned, archived=archived, deleted=deleted,
            sort_by=sort_by, sort_order=sort_order
        )
        return NoteListResponse(
            notes=[NoteResponse.model_validate(n) for n in notes],
            total_count=len(notes)
        )
