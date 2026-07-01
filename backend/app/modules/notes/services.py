from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from app.modules.notes.repository import NoteRepository
from app.models.notes import Note
from app.modules.notes.schemas import NoteCreate, NoteUpdate
from app.modules.notes.exceptions import (
    NoteNotFoundException,
    NoteAccessDeniedException,
    NoteValidationError
)

class NoteService:
    def __init__(self, repo: NoteRepository):
        self.repo = repo

    async def get_note(self, user_id: UUID, note_id: UUID, include_deleted: bool = False) -> Note:
        """
        Retrieves a singular entity structure, strictly validating ownership bounds.
        """
        note = await self.repo.get_by_id(note_id, include_deleted=include_deleted)
        if not note:
            raise NoteNotFoundException(note_id)
        if note.user_id != user_id:
            raise NoteAccessDeniedException(note_id, user_id)
        return note

    async def create_note(self, user_id: UUID, payload: NoteCreate) -> Note:
        """Enforces field combination structures and commits to data layer."""
        return await self.repo.create(user_id, payload.model_dump())

    async def update_note(self, user_id: UUID, note_id: UUID, payload: NoteUpdate) -> Note:
        """Enforces modification constraints against live, non-deleted nodes."""
        note = await self.get_note(user_id, note_id, include_deleted=False)

        update_dict = payload.model_dump(exclude_unset=True)
        return await self.repo.update(note, update_dict)

    async def delete_note(self, user_id: UUID, note_id: UUID) -> None:
        """Applies soft-delete timestamp markers to hide node from active indexes."""
        note = await self.get_note(user_id, note_id, include_deleted=False)
        await self.repo.soft_delete(note)

    async def restore_note(self, user_id: UUID, note_id: UUID) -> Note:
        """Clears soft-deletion parameters to restore node visibility."""
        note = await self.get_note(user_id, note_id, include_deleted=True)
        if not note.deleted_at:
            raise NoteValidationError("Target note is already active and cannot be restored.")
        return await self.repo.restore(note)

    async def toggle_archive_status(self, user_id: UUID, note_id: UUID, archive: bool) -> Note:
        """Alters specific utility flags without disrupting title or markdown bodies."""
        note = await self.get_note(user_id, note_id, include_deleted=False)
        return await self.repo.update(note, {"is_archived": archive})

    async def toggle_pin_status(self, user_id: UUID, note_id: UUID, pin: bool) -> Note:
        """Alters layout sorting weights independently of structural categorization tags."""
        note = await self.get_note(user_id, note_id, include_deleted=False)
        return await self.repo.update(note, {"is_pinned": pin})

    async def toggle_favorite_status(self, user_id: UUID, note_id: UUID, favorite: bool) -> Note:
        """Alters high-priority classification bookmarks independently of pinned parameters."""
        note = await self.get_note(user_id, note_id, include_deleted=False)
        return await self.repo.update(note, {"is_favorite": favorite})

    async def get_analytics(self, user_id: UUID) -> dict:
        return await self.repo.get_analytics(user_id)

    async def list_and_filter_notes(
        self,
        user_id: UUID,
        search: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        favorite: Optional[bool] = None,
        pinned: Optional[bool] = None,
        archived: Optional[bool] = False,
        deleted: bool = False,
        sort_by: str = "updated_at",
        sort_order: str = "desc"
    ) -> Sequence[Note]:
        """Orchestrates structured filtering arrays downstream to indexed datasets."""
        # Restrict sorting configurations to valid columns to prevent SQL injection attempts
        valid_sorts = ["updated_at", "created_at", "title"]
        if sort_by not in valid_sorts:
            sort_by = "updated_at"

        return await self.repo.list_and_filter(
            user_id=user_id,
            search=search,
            category=category,
            tag=tag,
            favorite=favorite,
            pinned=pinned,
            archived=archived,
            deleted=deleted,
            sort_by=sort_by,
            sort_order=sort_order
        )
