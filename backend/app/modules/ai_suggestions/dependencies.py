from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.modules.ai_suggestions.repository import AISuggestionRepository
from app.modules.ai_suggestions.services import AISuggestionService

security_scheme = HTTPBearer()


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> UUID:
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        return UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials context signature."
        )


async def get_ai_suggestion_service(
    db: AsyncSession = Depends(get_db),
) -> AISuggestionService:
    repo = AISuggestionRepository(db)
    return AISuggestionService(repo)
