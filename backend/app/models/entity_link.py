from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid6 import uuid7
from app.core.database import Base
from app.modules.entity_links.enums import RelationOrigin


class EntityLink(Base):
    __tablename__ = "entity_links"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid7)

    source_type = Column(String(50), index=True, nullable=False)
    source_id = Column(PG_UUID(as_uuid=True), index=True, nullable=False)

    target_type = Column(String(50), index=True, nullable=False)
    target_id = Column(PG_UUID(as_uuid=True), index=True, nullable=False)

    link_type = Column(String(50), nullable=False, default="RELATED_TO")

    relation_origin = Column(
        SQLEnum(RelationOrigin, name="relation_origin_enum"),
        nullable=False,
        default=RelationOrigin.USER,
    )

    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)
