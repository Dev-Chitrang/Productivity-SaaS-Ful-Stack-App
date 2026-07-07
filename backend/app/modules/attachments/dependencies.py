from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.providers import get_storage_service
from app.modules.attachments.repository import AttachmentRepository
from app.modules.attachments.service import AttachmentService

_security_scheme = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_security_scheme),
) -> UUID:
    """
    Decodes the Bearer token and returns the authenticated user UUID.
    Matches the same implementation used across all other modules.
    """
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"],
        )
        return UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials context signature.",
        )


def get_attachment_storage() -> StorageService:
    return get_storage_service("attachments")


async def get_attachment_service(
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_attachment_storage),
) -> AttachmentService:
    repo = AttachmentRepository(db)
    return AttachmentService(repo, storage)
