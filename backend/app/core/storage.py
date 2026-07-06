import os
import abc
from typing import BinaryIO, Optional
from uuid import UUID

import aiofiles
import magic

from app.core.config import settings
from app.modules.attachments.constants import ALLOWED_EXTENSIONS
from app.modules.attachments.exceptions import AttachmentValidationError

EXTENSION_TO_MIMES = {
    # Documents
    "pdf": {"application/pdf"},
    "doc": {"application/msword"},
    "docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
        "application/octet-stream",
    },
    "xls": {"application/vnd.ms-excel"},
    "xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/zip",
        "application/octet-stream",
    },
    "ppt": {"application/vnd.ms-powerpoint"},
    "pptx": {
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/zip",
        "application/octet-stream",
    },
    "txt": {"text/plain"},
    "rtf": {"text/rtf", "application/rtf", "text/plain"},
    "csv": {"text/csv", "text/plain", "application/csv", "application/octet-stream"},
    "odt": {"application/vnd.oasis.opendocument.text", "application/zip"},
    # Images
    "jpg": {"image/jpeg"},
    "jpeg": {"image/jpeg"},
    "png": {"image/png"},
    "gif": {"image/gif"},
    "webp": {"image/webp"},
    "svg": {"image/svg+xml", "text/xml", "application/xml", "image/svg"},
    "bmp": {"image/bmp", "image/x-ms-bmp"},
    "tiff": {"image/tiff"},
    # Audio
    "mp3": {"audio/mpeg", "audio/mp3", "audio/x-mpeg", "audio/mpeg3"},
    "wav": {"audio/wav", "audio/x-wav", "audio/wave"},
    "ogg": {"audio/ogg", "application/ogg", "video/ogg"},
    "m4a": {"audio/mp4", "audio/m4a", "audio/x-m4a"},
    "webm": {"audio/webm", "video/webm"},
    # Video
    "mp4": {"video/mp4", "audio/mp4"},
    "mov": {"video/quicktime"},
    "avi": {"video/x-msvideo", "video/avi", "video/msvideo"},
    "mkv": {"video/x-matroska", "video/matroska"},
    # Archives
    "zip": {"application/zip"},
    "tar": {"application/x-tar"},
    "gz": {"application/gzip", "application/x-gzip"},
    "7z": {"application/x-7z-compressed"},
    # Code / misc
    "md": {"text/markdown", "text/plain"},
}

def validate_uploaded_file(filename: str, content: bytes) -> str:
    # 1. Size check
    from app.modules.attachments.constants import MAX_ATTACHMENT_SIZE_BYTES
    size = len(content)
    if size == 0:
        raise AttachmentValidationError("Invalid file type.")
    if size > MAX_ATTACHMENT_SIZE_BYTES:
        raise AttachmentValidationError("File too large.")

    # 2. Extract and validate extension
    _, ext = os.path.splitext(filename)
    extension = ext.lstrip(".").lower()
    if not extension or extension not in ALLOWED_EXTENSIONS:
        raise AttachmentValidationError("Unsupported extension.")

    # 3. Detect MIME type using python-magic
    try:
        detected_mime = magic.from_buffer(content, mime=True)
    except Exception:
        raise AttachmentValidationError("Invalid file type.")

    if not detected_mime:
        raise AttachmentValidationError("Invalid file type.")

    detected_mime = detected_mime.lower().strip()

    # 4. Compare detected MIME with allowed MIME types for the extension
    allowed_mimes = EXTENSION_TO_MIMES.get(extension)
    if not allowed_mimes or detected_mime not in allowed_mimes:
        raise AttachmentValidationError("File contents do not match extension.")

    return detected_mime



class StorageProvider(abc.ABC):
    @abc.abstractmethod
    async def save(
        self,
        session_id: UUID,
        subfolder: str,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> dict:
        ...

    @abc.abstractmethod
    async def save_to_path(
        self,
        relative_dir: str,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> dict:
        """
        Generic save that accepts a caller-determined relative directory.
        The provider resolves it against its base directory.
        Returns {"storage_path": str, "size": int, "filename": str, "stored_filename": str}.
        """
        ...

    @abc.abstractmethod
    async def delete(self, storage_path: str) -> bool:
        ...

    @abc.abstractmethod
    def get_absolute_path(self, storage_path: str) -> str:
        ...

    @abc.abstractmethod
    def exists(self, storage_path: str) -> bool:
        ...


class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def _ensure_dir(self, path: str) -> str:
        os.makedirs(path, exist_ok=True)
        return path

    async def save(
        self,
        session_id: UUID,
        subfolder: str,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> dict:
        folder = self._ensure_dir(
            os.path.join(self.base_dir, str(session_id), subfolder)
        )
        safe_filename = f"{os.urandom(4).hex()}_{filename}"
        dest = os.path.join(folder, safe_filename)

        async with aiofiles.open(dest, "wb") as f:
            await f.write(content)

        return {
            "storage_path": dest,
            "size": os.path.getsize(dest),
            "filename": filename,
        }

    async def save_to_path(
        self,
        relative_dir: str,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> dict:
        """
        Generic save with a caller-supplied relative directory.
        A random 8-hex-char prefix is prepended to the filename to avoid
        collisions while preserving the original name in the stored value.
        """
        folder = self._ensure_dir(os.path.join(self.base_dir, relative_dir))
        stored_filename = f"{os.urandom(4).hex()}_{filename}"
        dest = os.path.join(folder, stored_filename)

        async with aiofiles.open(dest, "wb") as f:
            await f.write(content)

        return {
            "storage_path": dest,
            "size": os.path.getsize(dest),
            "filename": filename,
            "stored_filename": stored_filename,
        }

    async def delete(self, storage_path: str) -> bool:
        if os.path.exists(storage_path):
            os.remove(storage_path)
            return True
        return False

    def get_absolute_path(self, storage_path: str) -> str:
        return storage_path

    def exists(self, storage_path: str) -> bool:
        return os.path.exists(storage_path)


class StorageService:
    def __init__(self, provider: StorageProvider):
        self._provider = provider

    async def save_recording(
        self,
        session_id: UUID,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> dict:
        detected_mime = validate_uploaded_file(filename, content)
        result = await self._provider.save(
            session_id, "recordings", filename, content, detected_mime
        )
        result["content_type"] = detected_mime
        return result

    async def save_transcript(
        self,
        session_id: UUID,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> dict:
        detected_mime = validate_uploaded_file(filename, content)
        result = await self._provider.save(
            session_id, "transcripts", filename, content, detected_mime
        )
        result["content_type"] = detected_mime
        return result

    async def save_attachment(
        self,
        entity_type_dir: str,
        entity_id: str,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> dict:
        """
        Persists an attachment file under:
            <base_dir>/<entity_type_dir>/<entity_id>/<stored_filename>

        Returns the provider result dict including storage_path, size,
        filename, stored_filename, and content_type.
        """
        detected_mime = validate_uploaded_file(filename, content)
        relative_dir = os.path.join(entity_type_dir, entity_id)
        result = await self._provider.save_to_path(
            relative_dir, filename, content, detected_mime
        )
        result["content_type"] = detected_mime
        return result

    async def delete_file(self, storage_path: str) -> bool:
        return await self._provider.delete(storage_path)

    def get_absolute_path(self, storage_path: str) -> str:
        return self._provider.get_absolute_path(storage_path)

    def exists(self, storage_path: str) -> bool:
        return self._provider.exists(storage_path)
