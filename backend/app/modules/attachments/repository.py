from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attachment import Attachment
from app.modules.attachments.enums import AttachmentEntityType


class AttachmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Write operations ──────────────────────────────────────────────────────

    async def create(self, data: dict) -> Attachment:
        try:
            attachment = Attachment(**data)
            self.db.add(attachment)
            await self.db.flush()
            return attachment
        except Exception:
            await self.db.rollback()
            raise

    async def delete(self, attachment: Attachment) -> None:
        try:
            await self.db.delete(attachment)
            await self.db.flush()
        except Exception:
            await self.db.rollback()
            raise

    # ── Read operations ───────────────────────────────────────────────────────

    async def get_by_id(self, attachment_id: UUID) -> Optional[Attachment]:
        stmt = select(Attachment).where(Attachment.id == attachment_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_entity(
        self,
        entity_type: AttachmentEntityType,
        entity_id: UUID,
    ) -> Sequence[Attachment]:
        stmt = (
            select(Attachment)
            .where(
                and_(
                    Attachment.entity_type == entity_type,
                    Attachment.entity_id == entity_id,
                )
            )
            .order_by(Attachment.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def list_for_user(
        self,
        owner_user_id: UUID,
        entity_type: Optional[AttachmentEntityType] = None,
    ) -> Sequence[Attachment]:
        """List all attachments owned by a user, optionally filtered by entity type."""
        conditions = [Attachment.owner_user_id == owner_user_id]
        if entity_type is not None:
            conditions.append(Attachment.entity_type == entity_type)
        stmt = (
            select(Attachment)
            .where(and_(*conditions))
            .order_by(Attachment.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def stored_filename_exists(
        self,
        entity_type: AttachmentEntityType,
        entity_id: UUID,
        stored_filename: str,
    ) -> bool:
        """Guard against duplicate stored filenames within the same entity scope."""
        stmt = select(Attachment.id).where(
            and_(
                Attachment.entity_type == entity_type,
                Attachment.entity_id == entity_id,
                Attachment.stored_filename == stored_filename,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def delete_all_for_entity(
        self,
        entity_type: AttachmentEntityType,
        entity_id: UUID,
    ) -> Sequence[Attachment]:
        """
        Fetch and hard-delete every attachment record for the given entity.
        Returns the deleted records so the caller can remove the files from storage.
        """
        attachments = await self.list_for_entity(entity_type, entity_id)
        for attachment in attachments:
            try:
                await self.db.delete(attachment)
            except Exception:
                await self.db.rollback()
                raise
        if attachments:
            await self.db.flush()
        return list(attachments)
