from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid6 import uuid7
from app.core.database import Base
from app.modules.attachments.enums import AttachmentEntityType


class Attachment(Base):
    """
    Generic file attachment that can be owned by any entity in the system.

    Design notes
    ────────────
    • entity_type + entity_id form the logical owner composite key.  No FK is
      declared because each entity lives in a different table; referential
      integrity is enforced at the service layer.
    • owner_user_id is the authenticated user who uploaded the file, used for
      permission checks before module-specific authorisation is wired in.
    • stored_filename is the collision-safe name written to storage (random
      prefix + original name).  original_filename is what the user sees.
    • storage_provider is a free-form string tag ("local", "s3", …) so that
      future migrations to cloud storage do not require a schema change.
    • storage_path is the opaque path string interpreted by the active provider.
    """

    __tablename__ = "attachments"

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid7,
    )

    # ── Ownership ─────────────────────────────────────────────────────────────
    owner_user_id = Column(PG_UUID(as_uuid=True), index=True, nullable=False)

    entity_type = Column(
        SQLEnum(AttachmentEntityType, name="attachment_entity_type_enum"),
        index=True,
        nullable=False,
    )
    entity_id = Column(PG_UUID(as_uuid=True), index=True, nullable=False)

    # ── File identity ─────────────────────────────────────────────────────────
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(512), nullable=False)
    content_type = Column(String(127), nullable=False)
    extension = Column(String(20), nullable=False)
    size = Column(Integer, nullable=False)  # bytes

    # ── Storage ───────────────────────────────────────────────────────────────
    storage_provider = Column(String(50), nullable=False, default="local")
    storage_path = Column(String, nullable=False)

    # ── Audit ─────────────────────────────────────────────────────────────────
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
