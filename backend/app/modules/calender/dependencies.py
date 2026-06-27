from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.database import get_db
from app.core.redis import get_redis_client
from app.core.config import settings
from app.modules.calender.repository import CalendarRepository
from app.modules.calender.service import CalendarService

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

async def get_calendar_service(db: AsyncSession = Depends(get_db)) -> CalendarService:
    """
    Assembles the decoupled boundaries to supply a scoped Calendar service instance.
    """
    repo = CalendarRepository(db)
    return CalendarService(repo)
