import os
import abc
from typing import BinaryIO, Optional
from uuid import UUID

import aiofiles

from app.core.config import settings


class StorageProvider(abc.ABC):
    @abc.abstractmethod
    async def save(
        self,
        meeting_id: UUID,
        subfolder: str,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> dict:
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
        meeting_id: UUID,
        subfolder: str,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> dict:
        folder = self._ensure_dir(
            os.path.join(self.base_dir, str(meeting_id), subfolder)
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
        meeting_id: UUID,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> dict:
        return await self._provider.save(
            meeting_id, "recordings", filename, content, content_type
        )

    async def save_transcript(
        self,
        meeting_id: UUID,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> dict:
        return await self._provider.save(
            meeting_id, "transcripts", filename, content, content_type
        )

    async def delete_file(self, storage_path: str) -> bool:
        return await self._provider.delete(storage_path)

    def get_absolute_path(self, storage_path: str) -> str:
        return self._provider.get_absolute_path(storage_path)

    def exists(self, storage_path: str) -> bool:
        return self._provider.exists(storage_path)
