from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.meeting_suggested_task import MeetingSuggestedTask


class AISuggestionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> MeetingSuggestedTask:
        try:
            suggestion = MeetingSuggestedTask(**data)
            self.db.add(suggestion)
            await self.db.flush()
            return suggestion
        except Exception:
            await self.db.rollback()
            raise

    async def get_by_id(self, suggestion_id: UUID) -> Optional[MeetingSuggestedTask]:
        stmt = select(MeetingSuggestedTask).where(MeetingSuggestedTask.id == suggestion_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, suggestion: MeetingSuggestedTask, update_data: dict) -> MeetingSuggestedTask:
        try:
            for key, value in update_data.items():
                setattr(suggestion, key, value)
            self.db.add(suggestion)
            await self.db.flush()
            return suggestion
        except Exception:
            await self.db.rollback()
            raise

    async def list_by_analysis_id(self, analysis_id: UUID) -> Sequence[MeetingSuggestedTask]:
        stmt = (
            select(MeetingSuggestedTask)
            .where(MeetingSuggestedTask.analysis_id == analysis_id)
            .order_by(MeetingSuggestedTask.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def bulk_create(self, records: list[dict]) -> list[MeetingSuggestedTask]:
        try:
            suggestions = []
            for data in records:
                suggestion = MeetingSuggestedTask(**data)
                self.db.add(suggestion)
                suggestions.append(suggestion)
            await self.db.flush()
            return suggestions
        except Exception:
            await self.db.rollback()
            raise
