import uuid as _uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.core.providers import get_storage_service
from app.models.user import User
from app.modules.users.repository import UserRepository
from app.modules.calender.repository import CalendarRepository
from app.modules.calender.service import CalendarService
from app.modules.attachments.repository import AttachmentRepository
from app.modules.attachments.service import AttachmentService

security_scheme = HTTPBearer()

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> UUID:
    """
    Decodes the incoming Bearer JWT to extract the authenticated user identity boundary.
    Throws HTTP 401 if validation signatures fail.
    """
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        return UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials context signature."
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Resolves the full User object from the Bearer JWT.
    Used where the user's profile fields (e.g. timezone) are needed at the route level.
    """
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = payload["sub"]
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials context signature.",
        )
    repo = UserRepository(db)
    user = await repo.get_by_id(_uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


async def get_attachment_service(db: AsyncSession = Depends(get_db)) -> AttachmentService:
    """
    Assembles the AttachmentService scoped to the calendar module storage base directory.
    """
    repo = AttachmentRepository(db)
    storage = get_storage_service("attachments")
    return AttachmentService(repo, storage)


async def get_calendar_service(
    db: AsyncSession = Depends(get_db),
    attachment_svc: AttachmentService = Depends(get_attachment_service),
) -> CalendarService:
    """
    Assembles the decoupled boundaries to supply a scoped Calendar service instance.
    """
    repo = CalendarRepository(db)
    return CalendarService(repo, attachment_service=attachment_svc)
