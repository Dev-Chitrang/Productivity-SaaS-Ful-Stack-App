from datetime import datetime, timezone
from typing import Optional, Sequence, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update, asc, desc, func
from app.models.notes import Note

class NoteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: UUID, note_data: dict) -> Note:
        try:
            note = Note(user_id=user_id, **note_data)
            self.db.add(note)
            await self.db.flush()
            return note
        except Exception:
            await self.db.rollback()
            raise

    async def get_by_id(self, note_id: UUID, include_deleted: bool = False) -> Optional[Note]:
        conditions = [Note.id == note_id]
        if not include_deleted:
            conditions.append(Note.deleted_at.is_(None))

        stmt = select(Note).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, note: Note, update_data: dict) -> Note:
        try:
            for key, value in update_data.items():
                setattr(note, key, value)
            self.db.add(note)
            await self.db.flush()
            return note
        except Exception:
            await self.db.rollback()
            raise

    async def soft_delete(self, note: Note) -> None:
        try:
            note.deleted_at = datetime.now(timezone.utc)
            self.db.add(note)
            await self.db.flush()
        except Exception:
            await self.db.rollback()
            raise

    async def restore(self, note: Note) -> Note:
        try:
            note.deleted_at = None
            self.db.add(note)
            await self.db.flush()
            return note
        except Exception:
            await self.db.rollback()
            raise

    async def list_and_filter(
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
        # Filter matching visibility timelines
        conditions = [Note.user_id == user_id]

        if deleted:
            conditions.append(Note.deleted_at.is_not(None))
        else:
            conditions.append(Note.deleted_at.is_(None))

        # Explicit state filter mappings
        if archived is not None:
            conditions.append(Note.is_archived == archived)
        if favorite is not None:
            conditions.append(Note.is_favorite == favorite)
        if pinned is not None:
            conditions.append(Note.is_pinned == pinned)
        if category:
            conditions.append(func.lower(Note.category) == category.strip().lower())

        # JSONB containment evaluation strategy for exact tag intersections
        if tag:
            conditions.append(Note.tags.contains([tag.strip().lower()]))

        # Case-insensitive full text string block match evaluation
        if search:
            search_pattern = f"%{search.strip().lower()}%"
            conditions.append(
                or_(
                    func.lower(Note.title).ilike(search_pattern),
                    func.lower(Note.content).ilike(search_pattern)
                )
            )

        stmt = select(Note).where(and_(*conditions))

        # Dynamic Sorting Target Mapping Evaluation
        sort_column = getattr(Note, sort_by, Note.updated_at)
        if sort_order.lower() == "asc":
            stmt = stmt.order_by(asc(sort_column))
        else:
            stmt = stmt.order_by(desc(sort_column))

        result = await self.db.execute(stmt)
        return result.scalars().all()
