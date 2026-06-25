from fastapi import HTTPException, status
import logging
from app.modules.users.service import UserService
from app.modules.users.schemas import (
    UpdateProfileRequest, ChangePasswordRequest, ChangeEmailRequest,
    ProfileImageRequest, Toggle2FARequest
)
from app.core.logger import logger

class UserController:
    def __init__(self, service: UserService):
        self.service = service

    async def handle_get_profile(self, current_user_id: str):
        try:
            user = await self.service.get_profile(current_user_id)
            return {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_verified": user.is_verified,
                "is_2fa_enabled": user.is_2fa_enabled,
                "profile_image": user.profile_image,
                "timezone": user.timezone,
                "created_at": user.created_at
            }
        except ValueError as e:
            logger.error("get_profile_failed user_id=%s error=%s", current_user_id, str(e))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    async def handle_update_profile(self, current_user_id: str, payload: UpdateProfileRequest):
        try:
            user = await self.service.update_profile(current_user_id, payload.full_name, payload.timezone)
            logger.info("update_profile_success user_id=%s", current_user_id)
            return {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_verified": user.is_verified,
                "is_2fa_enabled": user.is_2fa_enabled,
                "profile_image": user.profile_image,
                "timezone": user.timezone,
                "created_at": user.created_at
            }
        except ValueError as e:
            logger.error("update_profile_failed user_id=%s error=%s", current_user_id, str(e))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    async def handle_change_password(self, current_user_id: str, payload: ChangePasswordRequest):
        try:
            await self.service.change_password(current_user_id, payload.current_password, payload.new_password)
            logger.info("change_password_success user_id=%s", current_user_id)
            return {"message": "Password changed successfully. Please log in again."}
        except ValueError as e:
            logger.error("change_password_failed user_id=%s error=%s", current_user_id, str(e))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except PermissionError as e:
            logger.error("change_password_failed user_id=%s error=%s", current_user_id, str(e))
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    async def handle_change_email(self, current_user_id: str, payload: ChangeEmailRequest):
        try:
            await self.service.change_email(current_user_id, payload.current_password, payload.new_email)
            logger.info("change_email_success user_id=%s new_email=%s", current_user_id, payload.new_email)
            return {"message": "Email changed successfully. Please log in again."}
        except ValueError as e:
            logger.error("change_email_failed user_id=%s error=%s", current_user_id, str(e))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except PermissionError as e:
            logger.error("change_email_failed user_id=%s error=%s", current_user_id, str(e))
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    async def handle_update_profile_image(self, current_user_id: str, payload: ProfileImageRequest):
        try:
            user = await self.service.update_profile_image(current_user_id, payload.profile_image)
            logger.info("update_profile_image_success user_id=%s", current_user_id)
            return {"message": "Profile image updated successfully.", "profile_image": user.profile_image}
        except ValueError as e:
            logger.error("update_profile_image_failed user_id=%s error=%s", current_user_id, str(e))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    async def handle_toggle_2fa(self, current_user_id: str, payload: Toggle2FARequest):
        try:
            user = await self.service.toggle_2fa(current_user_id, payload.enable)
            logger.info("toggle_2fa_success user_id=%s enable=%s", current_user_id, payload.enable)
            return {"message": "2FA settings updated.", "is_2fa_enabled": user.is_2fa_enabled}
        except ValueError as e:
            logger.error("toggle_2fa_failed user_id=%s error=%s", current_user_id, str(e))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    async def handle_deactivate(self, current_user_id: str):
        try:
            await self.service.deactivate_account(current_user_id)
            logger.info("deactivate_account_success user_id=%s", current_user_id)
            return {"message": "Account successfully deactivated."}
        except ValueError as e:
            logger.error("deactivate_account_failed user_id=%s error=%s", current_user_id, str(e))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
