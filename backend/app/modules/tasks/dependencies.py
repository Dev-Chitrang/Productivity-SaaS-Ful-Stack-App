from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.core.providers import get_storage_service
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.services import TaskService
from app.modules.attachments.repository import AttachmentRepository
from app.modules.attachments.service import AttachmentService

security_scheme = HTTPBearer()

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> UUID:
    """
    Decodes and validates the active session signature to extract the user's UUID.
    """
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        return UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials context signature."
        )

async def get_attachment_service(db: AsyncSession = Depends(get_db)) -> AttachmentService:
    """
    Assembles the AttachmentService scoped to the task module's storage base directory.
    """
    repo = AttachmentRepository(db)
    storage = get_storage_service("attachments")
    return AttachmentService(repo, storage)

async def get_tasks_service(
    db: AsyncSession = Depends(get_db),
    attachment_svc: AttachmentService = Depends(get_attachment_service),
) -> TaskService:
    """
    Assembles a structurally isolated instance of the TaskService domain provider.
    """
    repo = TaskRepository(db)
    return TaskService(repo, attachment_service=attachment_svc)
