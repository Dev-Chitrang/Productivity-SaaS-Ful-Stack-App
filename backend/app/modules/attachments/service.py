import os
import re
import unicodedata
from typing import Optional, Sequence
from uuid import UUID

from fastapi import UploadFile

from app.core.storage import StorageService
from app.models.attachment import Attachment
from app.modules.attachments.constants import (
    ALLOWED_CONTENT_TYPES,
    ALLOWED_EXTENSIONS,
    MAX_ATTACHMENT_SIZE_BYTES,
    MAX_FILENAME_LENGTH,
)
from app.modules.attachments.enums import AttachmentEntityType, ENTITY_STORAGE_DIRS
from app.modules.attachments.exceptions import (
    AttachmentAccessDeniedException,
    AttachmentNotFoundException,
    AttachmentStorageError,
    AttachmentValidationError,
)
from app.modules.attachments.repository import AttachmentRepository


# ── Filename sanitisation ─────────────────────────────────────────────────────

_UNSAFE_CHARS = re.compile(r'[^\w\s\-.]', re.UNICODE)
_MULTI_SPACES = re.compile(r'\s+')
_LEADING_DOTS = re.compile(r'^\.+')


def _sanitise_filename(raw: str) -> str:
    """
    Return a filesystem-safe filename.

    Steps:
      1. Unicode-normalise (NFC) to collapse combining characters.
      2. Strip control characters and characters outside \\w / - / . / space.
      3. Collapse repeated whitespace to a single underscore.
      4. Strip leading dots (hidden-file prevention).
      5. Truncate to MAX_FILENAME_LENGTH.
      6. Fall back to "attachment" when nothing survives.
    """
    name = unicodedata.normalize("NFC", raw.strip())
    name = _UNSAFE_CHARS.sub("", name)
    name = _MULTI_SPACES.sub("_", name).strip("_")
    name = _LEADING_DOTS.sub("", name)
    name = name[:MAX_FILENAME_LENGTH]
    return name or "attachment"


def _extract_extension(filename: str) -> str:
    """Return the lower-case extension without the leading dot, or empty string."""
    _, ext = os.path.splitext(filename)
    return ext.lstrip(".").lower()


# ── Service ───────────────────────────────────────────────────────────────────

class AttachmentService:
    def __init__(self, repo: AttachmentRepository, storage: StorageService):
        self.repo = repo
        self.storage = storage

    # ── Upload ────────────────────────────────────────────────────────────────

    async def upload(
        self,
        owner_user_id: UUID,
        entity_type: AttachmentEntityType,
        entity_id: UUID,
        file: UploadFile,
    ) -> Attachment:
        """
        Validate, persist to storage, and record metadata in the database.

        Validation order (fail-fast):
          1. Filename present and safe.
          2. Extension allowed.
          3. Content-Type declared and allowed.
          4. File size within limit.
        """
        # 1. Filename validation & sanitisation
        raw_name = file.filename or ""
        if not raw_name.strip():
            raise AttachmentValidationError("A filename is required.")

        original_filename = _sanitise_filename(raw_name)
        extension = _extract_extension(original_filename)

        if not extension:
            raise AttachmentValidationError(
                "The uploaded file must have a recognisable extension."
            )
        if extension not in ALLOWED_EXTENSIONS:
            raise AttachmentValidationError(
                f"File type '.{extension}' is not permitted. "
                f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
            )

        # 2. Content-Type validation
        declared_ct = (file.content_type or "application/octet-stream").lower().strip()
        # Strip charset suffix (e.g. "text/plain; charset=utf-8" → "text/plain")
        content_type = declared_ct.split(";")[0].strip()
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise AttachmentValidationError(
                f"Content type '{content_type}' is not permitted."
            )

        # 3. Read content and validate size
        content = await file.read()
        size = len(content)
        if size == 0:
            raise AttachmentValidationError("Empty files cannot be uploaded.")
        if size > MAX_ATTACHMENT_SIZE_BYTES:
            limit_mb = MAX_ATTACHMENT_SIZE_BYTES // (1024 * 1024)
            raise AttachmentValidationError(
                f"File exceeds the maximum allowed size of {limit_mb} MB."
            )

        # 4. Persist to storage
        entity_dir = ENTITY_STORAGE_DIRS[entity_type]
        try:
            result = await self.storage.save_attachment(
                entity_type_dir=entity_dir,
                entity_id=str(entity_id),
                filename=original_filename,
                content=content,
                content_type=content_type,
            )
        except Exception as exc:
            raise AttachmentStorageError(
                f"Failed to persist attachment to storage: {exc}"
            ) from exc

        stored_filename: str = result["stored_filename"]

        # 5. Guard against stored-filename collision (extremely unlikely but explicit)
        if await self.repo.stored_filename_exists(entity_type, entity_id, stored_filename):
            # Re-trigger a new upload attempt with a fresh random prefix
            try:
                result = await self.storage.save_attachment(
                    entity_type_dir=entity_dir,
                    entity_id=str(entity_id),
                    filename=original_filename,
                    content=content,
                    content_type=content_type,
                )
                stored_filename = result["stored_filename"]
            except Exception as exc:
                raise AttachmentStorageError(
                    f"Storage collision retry failed: {exc}"
                ) from exc

        # 6. Write metadata record
        record = await self.repo.create(
            {
                "owner_user_id": owner_user_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "original_filename": original_filename,
                "stored_filename": stored_filename,
                "content_type": content_type,
                "extension": extension,
                "size": result["size"],
                "storage_provider": "local",
                "storage_path": result["storage_path"],
            }
        )
        return record

    # ── Download / metadata ───────────────────────────────────────────────────

    async def get_metadata(
        self, attachment_id: UUID, owner_user_id: UUID
    ) -> Attachment:
        attachment = await self._fetch_and_authorise(attachment_id, owner_user_id)
        return attachment

    async def get_for_download(
        self, attachment_id: UUID, owner_user_id: UUID
    ) -> Attachment:
        """Return the attachment after verifying ownership and storage existence."""
        attachment = await self._fetch_and_authorise(attachment_id, owner_user_id)
        if not self.storage.exists(attachment.storage_path):
            raise AttachmentNotFoundException(attachment_id)
        return attachment

    async def list_for_entity(
        self,
        entity_type: AttachmentEntityType,
        entity_id: UUID,
        owner_user_id: UUID,
    ) -> Sequence[Attachment]:
        """
        Return all attachments for an entity.
        Owner check: only the uploader can list attachments at this generic layer.
        Module-specific integration will replace this with richer authorisation.
        """
        attachments = await self.repo.list_for_entity(entity_type, entity_id)
        # Filter to what the requesting user owns (generic layer — no cross-entity checks yet)
        return [a for a in attachments if a.owner_user_id == owner_user_id]

    async def list_all_for_entity(
        self,
        entity_type: AttachmentEntityType,
        entity_id: UUID,
    ) -> Sequence[Attachment]:
        """
        Return ALL attachments for an entity without owner filtering.
        Used by module-specific integrations that have already verified
        entity-level access through the module's own authorization layer.
        """
        return await self.repo.list_for_entity(entity_type, entity_id)

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete(self, attachment_id: UUID, owner_user_id: UUID) -> None:
        attachment = await self._fetch_and_authorise(attachment_id, owner_user_id)
        # Best-effort storage deletion — log but do not hard-fail if file is missing
        try:
            await self.storage.delete_file(attachment.storage_path)
        except Exception:
            pass
        await self.repo.delete(attachment)

    async def get_for_download_verified(
        self, attachment_id: UUID, entity_type: AttachmentEntityType, entity_id: UUID
    ) -> Attachment:
        """
        Return the attachment for download after verifying it belongs to the
        given entity (not a specific user).  Used by module-specific routes
        that have already confirmed entity-level access.
        """
        attachment = await self.repo.get_by_id(attachment_id)
        if not attachment:
            raise AttachmentNotFoundException(attachment_id)
        if attachment.entity_type != entity_type or attachment.entity_id != entity_id:
            raise AttachmentNotFoundException(attachment_id)
        if not self.storage.exists(attachment.storage_path):
            raise AttachmentNotFoundException(attachment_id)
        return attachment

    async def delete_verified(
        self, attachment_id: UUID, entity_type: AttachmentEntityType, entity_id: UUID
    ) -> None:
        """
        Delete an attachment after verifying it belongs to the given entity.
        Used by module-specific routes that have already confirmed entity-level access.
        """
        attachment = await self.repo.get_by_id(attachment_id)
        if not attachment:
            raise AttachmentNotFoundException(attachment_id)
        if attachment.entity_type != entity_type or attachment.entity_id != entity_id:
            raise AttachmentNotFoundException(attachment_id)
        try:
            await self.storage.delete_file(attachment.storage_path)
        except Exception:
            pass
        await self.repo.delete(attachment)

    # ── Bulk entity cleanup (called on parent entity deletion) ────────────────

    async def delete_all_for_entity(
        self,
        entity_type: AttachmentEntityType,
        entity_id: UUID,
    ) -> None:
        """
        Remove every attachment belonging to an entity — both storage files and DB records.
        Called during cascade deletion of a parent entity (task, event, session).
        Storage errors are swallowed per-file so a missing file never blocks the DB cleanup.
        """
        deleted_records = await self.repo.delete_all_for_entity(entity_type, entity_id)
        for record in deleted_records:
            try:
                await self.storage.delete_file(record.storage_path)
            except Exception:
                pass

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _fetch_and_authorise(
        self, attachment_id: UUID, owner_user_id: UUID
    ) -> Attachment:
        attachment = await self.repo.get_by_id(attachment_id)
        if not attachment:
            raise AttachmentNotFoundException(attachment_id)
        if attachment.owner_user_id != owner_user_id:
            raise AttachmentAccessDeniedException(attachment_id, owner_user_id)
        return attachment
