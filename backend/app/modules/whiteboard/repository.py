from typing import Optional, Sequence
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.whiteboard import Whiteboard
from app.modules.whiteboard.schemas import WhiteboardFilters

class WhiteboardRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: UUID, data: dict) -> Whiteboard:
        board = Whiteboard(user_id=user_id, **data)
        self.db.add(board)
        await self.db.flush()
        return board

    async def get_by_id(self, board_id: UUID) -> Optional[Whiteboard]:
        stmt = select(Whiteboard).where(Whiteboard.id == board_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, board: Whiteboard, update_data: dict) -> Whiteboard:
        for key, value in update_data.items():
            setattr(board, key, value)
        self.db.add(board)
        await self.db.flush()
        return board

    async def list_boards(self, user_id: UUID, filters: WhiteboardFilters) -> Sequence[Whiteboard]:
        conditions = [Whiteboard.user_id == user_id]

        # Apply lifecycle and feature flags
        conditions.append(Whiteboard.is_archived == filters.is_archived)
        conditions.append(Whiteboard.is_deleted == filters.is_deleted)

        if filters.is_favorite is not None:
            conditions.append(Whiteboard.is_favorite == filters.is_favorite)

        # Vectorized textual containment search matching title elements strictly
        if filters.search:
            conditions.append(
                func.lower(Whiteboard.title).contains(filters.search.strip().lower())
            )

        stmt = select(Whiteboard).where(and_(*conditions)).order_by(Whiteboard.updated_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()
