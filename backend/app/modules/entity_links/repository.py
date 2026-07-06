from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.entity_link import EntityLink


class EntityLinkRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> EntityLink:
        try:
            link = EntityLink(**data)
            self.db.add(link)
            await self.db.flush()
            return link
        except Exception:
            await self.db.rollback()
            raise

    async def get_by_id(self, link_id: UUID, include_deleted: bool = False) -> Optional[EntityLink]:
        stmt = select(EntityLink).where(EntityLink.id == link_id)
        if not include_deleted:
            stmt = stmt.where(EntityLink.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def soft_delete(self, link: EntityLink) -> None:
        try:
            link.deleted_at = datetime.now(timezone.utc)
            self.db.add(link)
            await self.db.flush()
        except Exception:
            await self.db.rollback()
            raise

    async def list_links(
        self,
        source_type: Optional[str] = None,
        source_id: Optional[UUID] = None,
        target_type: Optional[str] = None,
        target_id: Optional[UUID] = None,
        include_deleted: bool = False,
    ) -> Sequence[EntityLink]:
        conditions = []
        if not include_deleted:
            conditions.append(EntityLink.deleted_at.is_(None))
        if source_type:
            conditions.append(EntityLink.source_type == source_type)
        if source_id:
            conditions.append(EntityLink.source_id == source_id)
        if target_type:
            conditions.append(EntityLink.target_type == target_type)
        if target_id:
            conditions.append(EntityLink.target_id == target_id)

        stmt = select(EntityLink).where(and_(*conditions)).order_by(EntityLink.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def soft_delete_by_entity(self, entity_type: str, entity_id: UUID) -> None:
        try:
            stmt = select(EntityLink).where(
                and_(
                    EntityLink.deleted_at.is_(None),
                    or_(
                        and_(EntityLink.source_type == entity_type, EntityLink.source_id == entity_id),
                        and_(EntityLink.target_type == entity_type, EntityLink.target_id == entity_id),
                    ),
                )
            )
            result = await self.db.execute(stmt)
            links = result.scalars().all()
            now = datetime.now(timezone.utc)
            for link in links:
                link.deleted_at = now
                self.db.add(link)
            await self.db.flush()
        except Exception:
            await self.db.rollback()
            raise
