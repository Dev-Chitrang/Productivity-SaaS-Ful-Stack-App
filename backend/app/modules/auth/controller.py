from fastapi import HTTPException, status
import logging
from app.modules.auth.service import AuthService
from app.modules.auth.schema import (
    UserRegisterRequest, OTPVerificationRequest, UserLoginRequest,
    TokenRefreshRequest, PasswordResetInitiate, PasswordResetConfirm,
    ResendOtpRequest, TokenResponse, GoogleOAuthRequest
)
from app.core.logger import logger

class AuthController:
    def __init__(self, service: AuthService):
        self.service = service

    async def handle_google_oauth(self, payload: GoogleOAuthRequest):
        try:
            logger.info("auth_google_oauth initiated")
            result = await self.service.authenticate_with_google(payload.id_token)
            if result.get("requires_2fa"):
                logger.info("auth_google_oauth_2fa_required")
                return {"requires_2fa": True, "verification_token": result["verification_token"]}
            logger.info("auth_google_oauth_success")
            return result
        except PermissionError as e:
            logger.error("auth_google_oauth_failed error=%s", str(e))
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
        except ValueError as e:
            logger.error("auth_google_oauth_failed error=%s", str(e))
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def handle_signup(self, payload: UserRegisterRequest):
        try:
            logger.info("auth_signup email=%s", payload.email)
            verification_token = await self.service.register_user(
                payload.email, payload.password, payload.full_name, payload.enable_2fa
            )
            logger.info("auth_signup_success email=%s", payload.email)
            return {"verification_token": verification_token, "message": "Verification code sent to email."}
        except ValueError as e:
            logger.error("auth_signup_failed email=%s error=%s", payload.email, str(e))
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def handle_verify_signup(self, payload: OTPVerificationRequest):
        try:
            return await self.service.verify_registration_otp(payload.verification_token, payload.code)
        except PermissionError as e:
            logger.error("auth_verify_signup_failed token=%s error=%s", payload.verification_token, str(e))
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
        except ValueError as e:
            logger.error("auth_verify_signup_failed token=%s error=%s", payload.verification_token, str(e))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    async def handle_resend_signup_otp(self, payload: ResendOtpRequest):
        try:
            logger.info("auth_resend_signup_otp token=%s", payload.verification_token)
            await self.service.resend_signup_otp(payload.verification_token)
            logger.info("auth_resend_signup_otp_success token=%s", payload.verification_token)
            return {"message": "Verification code resent successfully."}
        except ValueError as e:
            logger.error("auth_resend_signup_otp_failed token=%s error=%s", payload.verification_token, str(e))
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def handle_login(self, payload: UserLoginRequest):
        try:
            logger.info("auth_login email=%s", payload.email)
            result = await self.service.login_step_one(payload.email, payload.password)
            if result.get("requires_2fa"):
                logger.info("auth_login_2fa_required email=%s", payload.email)
                return {"requires_2fa": True, "verification_token": result["verification_token"]}
            logger.info("auth_login_success email=%s", payload.email)
            return result
        except PermissionError as e:
            logger.error("auth_login_failed email=%s error=%s", payload.email, str(e))
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
        except ValueError as e:
            logger.error("auth_login_failed email=%s error=%s", payload.email, str(e))
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def handle_verify_login(self, payload: OTPVerificationRequest):
        try:
            return await self.service.verify_login_otp(payload.verification_token, payload.code)
        except PermissionError as e:
            logger.error("auth_verify_login_failed token=%s error=%s", payload.verification_token, str(e))
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
        except ValueError as e:
            logger.error("auth_verify_login_failed token=%s error=%s", payload.verification_token, str(e))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    async def handle_resend_login_otp(self, payload: ResendOtpRequest):
        try:
            logger.info("auth_resend_login_otp token=%s", payload.verification_token)
            await self.service.resend_login_otp(payload.verification_token)
            logger.info("auth_resend_login_otp_success token=%s", payload.verification_token)
            return {"message": "Login verification code resent successfully."}
        except ValueError as e:
            logger.error("auth_resend_login_otp_failed token=%s error=%s", payload.verification_token, str(e))
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def handle_refresh(self, payload: TokenRefreshRequest):
        try:
            return await self.service.refresh_access_session(payload.refresh_token)
        except PermissionError as e:
            logger.error("auth_refresh_failed error=%s", str(e))
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    async def handle_password_reset_request(self, payload: PasswordResetInitiate):
        try:
            logger.info("auth_password_reset_initiate email=%s", payload.email)
            await self.service.initiate_password_reset(payload.email)
            logger.info("auth_password_reset_initiate_success email=%s", payload.email)
            return {"message": "If records match, processing vectors have background initialized."}
        except PermissionError as e:
            logger.error("auth_password_reset_initiate_failed email=%s error=%s", payload.email, str(e))
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    async def handle_password_reset_confirm(self, payload: PasswordResetConfirm):
        try:
            logger.info("auth_password_reset_confirm token=%s", payload.token)
            await self.service.execute_password_reset(payload.token, payload.new_password)
            logger.info("auth_password_reset_confirm_success token=%s", payload.token)
            return {"message": "Password updated successfully. Active cached sessions revoked."}
        except PermissionError as e:
            logger.error("auth_password_reset_confirm_failed token=%s error=%s", payload.token, str(e))
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except ValueError as e:
            logger.error("auth_password_reset_confirm_failed token=%s error=%s", payload.token, str(e))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
