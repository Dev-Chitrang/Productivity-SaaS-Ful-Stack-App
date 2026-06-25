import uuid
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.modules.users.repository import UserRepository

security_agent = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security_agent),
    db: AsyncSession = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = payload["sub"]
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token parameters.")

    repo = UserRepository(db)
    user = await repo.get_by_id(uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user
