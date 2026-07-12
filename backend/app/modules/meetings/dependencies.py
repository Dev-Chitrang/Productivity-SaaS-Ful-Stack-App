from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.http import HTTPAuthorizationCredentials
from starlette.requests import HTTPConnection, Request
import jwt
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.database import get_db
from app.core.config import settings
from app.core.providers import get_storage_service as get_provider_storage_service
from app.core.storage import StorageService
from app.core.redis import get_redis_client
from app.modules.meetings.repository import MeetingRepository, MeetingSessionRepository
from app.modules.meetings.service import MeetingService, MeetingSessionService
from app.modules.meetings.authorization import SessionAuthorizationService
from app.modules.attachments.repository import AttachmentRepository
from app.modules.attachments.service import AttachmentService

class WSCompatibleBearer(HTTPBearer):
    async def __call__(self, request: HTTPConnection):
        # HTTPBearer parent needs a real Request; WebSocket is HTTPConnection only
        if isinstance(request, Request):
            return await super().__call__(request)
        # WebSocket path: parse Authorization header manually
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            if self.auto_error:
                raise HTTPException(status_code=403, detail="Not authenticated")
            return None
        return HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=authorization[7:]
        )

security_scheme = WSCompatibleBearer()
optional_security_scheme = WSCompatibleBearer(auto_error=False)

def get_meeting_storage() -> StorageService:
    return get_provider_storage_service("meetings")

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> UUID:
    """
    Validates security signature context frames to identify the current system User ID.
    """
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        return UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials context signature."
        )

def get_optional_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security_scheme)) -> Optional[UUID]:
    """
    Optional authentication handler allowing seamless guest flow fallback down inside routers.
    """
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        return UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError):
        return None

async def get_meetings_service(
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_meeting_storage),
    redis: Redis = Depends(get_redis_client),
) -> MeetingService:
    """
    Assembles a structurally isolated instance of the MeetingService layer.
    """
    repo = MeetingRepository(db)
    session_repo = MeetingSessionRepository(db)
    session_service = MeetingSessionService(session_repo, redis, meeting_repo=repo)
    auth_service = SessionAuthorizationService(repo, session_repo)
    return MeetingService(repo, storage, session_service, auth_service)


async def get_attachment_service(db: AsyncSession = Depends(get_db)) -> AttachmentService:
    """
    Assembles the AttachmentService scoped to the meetings module storage directory.
    """
    repo = AttachmentRepository(db)
    storage = get_provider_storage_service("attachments")
    return AttachmentService(repo, storage)
