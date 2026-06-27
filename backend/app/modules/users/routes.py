from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.database import get_db
from app.core.redis import get_redis_client
from app.modules.users.dependencies import get_current_user
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService
from app.modules.users.controller import UserController
from app.modules.users.schemas import (
    UpdateProfileRequest, ChangePasswordRequest, ChangeEmailRequest,
    ProfileImageRequest, Toggle2FARequest
)
from app.models.user import User

router = APIRouter(prefix="/users", tags=["User Profile Management"])

async def get_controller(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_client)
) -> UserController:
    repo = UserRepository(db)
    service = UserService(repo, redis)
    return UserController(service)

@router.get("/me")
async def get_profile_route(
    current_user: User = Depends(get_current_user),
    ctrl: UserController = Depends(get_controller)
):
    return await ctrl.handle_get_profile(str(current_user.id))

@router.put("/profile")
async def update_profile_route(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    ctrl: UserController = Depends(get_controller)
):
    return await ctrl.handle_update_profile(str(current_user.id), payload)

@router.put("/change-password")
async def change_password_route(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    ctrl: UserController = Depends(get_controller)
):
    return await ctrl.handle_change_password(str(current_user.id), payload)

@router.put("/change-email")
async def change_email_route(
    payload: ChangeEmailRequest,
    current_user: User = Depends(get_current_user),
    ctrl: UserController = Depends(get_controller)
):
    return await ctrl.handle_change_email(str(current_user.id), payload)

@router.put("/profile-image")
async def update_profile_image_route(
    payload: ProfileImageRequest,
    current_user: User = Depends(get_current_user),
    ctrl: UserController = Depends(get_controller)
):
    return await ctrl.handle_update_profile_image(str(current_user.id), payload)

@router.put("/2fa")
async def toggle_2fa_route(
    payload: Toggle2FARequest,
    current_user: User = Depends(get_current_user),
    ctrl: UserController = Depends(get_controller)
):
    return await ctrl.handle_toggle_2fa(str(current_user.id), payload)

@router.delete("/deactivate")
async def deactivate_route(
    current_user: User = Depends(get_current_user),
    ctrl: UserController = Depends(get_controller)
):
    return await ctrl.handle_deactivate(str(current_user.id))
