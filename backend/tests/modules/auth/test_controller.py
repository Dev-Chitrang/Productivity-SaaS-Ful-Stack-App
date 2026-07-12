import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException, status
from app.modules.auth.service import AuthService
from app.modules.auth.controller import AuthController
from app.modules.auth.schema import (
    UserRegisterRequest,
    OTPVerificationRequest,
    UserLoginRequest,
    TokenRefreshRequest,
    PasswordResetInitiate,
    PasswordResetConfirm,
    ResendOtpRequest,
    GoogleOAuthRequest,
)


class TestAuthController:
    @pytest.fixture
    def controller(self):
        service = MagicMock(spec=AuthService)
        return AuthController(service)

    async def test_handle_google_oauth_success(self, controller):
        controller.service.authenticate_with_google.return_value = {
            "access_token": "acc",
            "refresh_token": "ref",
            "token_type": "bearer",
            "requires_2fa": False,
        }
        payload = GoogleOAuthRequest(id_token="google_token")
        result = await controller.handle_google_oauth(payload)
        assert result["access_token"] == "acc"
        controller.service.authenticate_with_google.assert_called_once_with("google_token")

    async def test_handle_google_oauth_2fa_required(self, controller):
        controller.service.authenticate_with_google.return_value = {
            "requires_2fa": True,
            "verification_token": "vtok_123",
        }
        payload = GoogleOAuthRequest(id_token="google_token")
        result = await controller.handle_google_oauth(payload)
        assert result["requires_2fa"] is True
        assert result["verification_token"] == "vtok_123"

    async def test_handle_google_oauth_permission_error(self, controller):
        controller.service.authenticate_with_google.side_effect = PermissionError("invalid token")
        payload = GoogleOAuthRequest(id_token="bad_token")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_google_oauth(payload)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_handle_google_oauth_value_error(self, controller):
        controller.service.authenticate_with_google.side_effect = ValueError("bad request")
        payload = GoogleOAuthRequest(id_token="bad_token")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_google_oauth(payload)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_handle_signup_success(self, controller):
        controller.service.register_user.return_value = "verification_token_abc"
        payload = UserRegisterRequest(
            email="new@example.com",
            password="SecurePass123!",
            full_name="New User",
        )
        result = await controller.handle_signup(payload)
        assert result["verification_token"] == "verification_token_abc"
        assert "Verification code sent" in result["message"]
        controller.service.register_user.assert_called_once_with(
            "new@example.com", "SecurePass123!", "New User", False
        )

    async def test_handle_signup_value_error(self, controller):
        controller.service.register_user.side_effect = ValueError("email exists")
        payload = UserRegisterRequest(
            email="existing@example.com",
            password="SecurePass123!",
            full_name="Existing",
        )
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_signup(payload)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_handle_verify_signup_success(self, controller):
        controller.service.verify_registration_otp.return_value = {
            "access_token": "acc",
            "refresh_token": "ref",
        }
        payload = OTPVerificationRequest(verification_token="vtok", code="123456")
        result = await controller.handle_verify_signup(payload)
        assert result["access_token"] == "acc"

    async def test_handle_verify_signup_permission_error(self, controller):
        controller.service.verify_registration_otp.side_effect = PermissionError("invalid code")
        payload = OTPVerificationRequest(verification_token="vtok", code="000000")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_verify_signup(payload)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_handle_verify_signup_value_error(self, controller):
        controller.service.verify_registration_otp.side_effect = ValueError("not found")
        payload = OTPVerificationRequest(verification_token="vtok", code="123456")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_verify_signup(payload)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_handle_resend_signup_otp_success(self, controller):
        controller.service.resend_signup_otp.return_value = None
        payload = ResendOtpRequest(verification_token="vtok_abc")
        result = await controller.handle_resend_signup_otp(payload)
        assert "resent" in result["message"].lower()

    async def test_handle_resend_signup_otp_value_error(self, controller):
        controller.service.resend_signup_otp.side_effect = ValueError("session expired")
        payload = ResendOtpRequest(verification_token="expired")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_resend_signup_otp(payload)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_handle_login_success(self, controller):
        controller.service.login_step_one.return_value = {
            "access_token": "acc",
            "refresh_token": "ref",
            "requires_2fa": False,
        }
        payload = UserLoginRequest(email="user@example.com", password="password123")
        result = await controller.handle_login(payload)
        assert result["access_token"] == "acc"
        controller.service.login_step_one.assert_called_once_with(
            "user@example.com", "password123"
        )

    async def test_handle_login_2fa_required(self, controller):
        controller.service.login_step_one.return_value = {
            "requires_2fa": True,
            "verification_token": "vtok_login",
        }
        payload = UserLoginRequest(email="user@example.com", password="password123")
        result = await controller.handle_login(payload)
        assert result["requires_2fa"] is True

    async def test_handle_login_permission_error(self, controller):
        controller.service.login_step_one.side_effect = PermissionError("WRONG_PASSWORD")
        payload = UserLoginRequest(email="user@example.com", password="wrong")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_login(payload)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_handle_login_value_error(self, controller):
        controller.service.login_step_one.side_effect = ValueError("ACCOUNT_UNVERIFIED")
        payload = UserLoginRequest(email="user@example.com", password="password")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_login(payload)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_handle_verify_login_success(self, controller):
        controller.service.verify_login_otp.return_value = {
            "access_token": "acc",
            "refresh_token": "ref",
        }
        payload = OTPVerificationRequest(verification_token="vtok", code="123456")
        result = await controller.handle_verify_login(payload)
        assert result["access_token"] == "acc"

    async def test_handle_verify_login_permission_error(self, controller):
        controller.service.verify_login_otp.side_effect = PermissionError("invalid code")
        payload = OTPVerificationRequest(verification_token="vtok", code="000000")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_verify_login(payload)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_handle_verify_login_value_error(self, controller):
        controller.service.verify_login_otp.side_effect = ValueError("not found")
        payload = OTPVerificationRequest(verification_token="vtok", code="123456")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_verify_login(payload)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_handle_resend_login_otp_success(self, controller):
        controller.service.resend_login_otp.return_value = None
        payload = ResendOtpRequest(verification_token="vtok")
        result = await controller.handle_resend_login_otp(payload)
        assert "resent" in result["message"].lower()

    async def test_handle_resend_login_otp_value_error(self, controller):
        controller.service.resend_login_otp.side_effect = ValueError("expired")
        payload = ResendOtpRequest(verification_token="expired")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_resend_login_otp(payload)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_handle_refresh_success(self, controller):
        controller.service.refresh_access_session.return_value = {
            "access_token": "new_acc",
            "refresh_token": "new_ref",
        }
        payload = TokenRefreshRequest(refresh_token="refresh_abc")
        result = await controller.handle_refresh(payload)
        assert result["access_token"] == "new_acc"
        controller.service.refresh_access_session.assert_called_once_with("refresh_abc")

    async def test_handle_refresh_permission_error(self, controller):
        controller.service.refresh_access_session.side_effect = PermissionError(
            "session expired"
        )
        payload = TokenRefreshRequest(refresh_token="refresh_abc")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_refresh(payload)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_handle_password_reset_request_success(self, controller):
        controller.service.initiate_password_reset.return_value = None
        payload = PasswordResetInitiate(email="user@example.com")
        result = await controller.handle_password_reset_request(payload)
        assert "background initialized" in result["message"].lower()
        controller.service.initiate_password_reset.assert_called_once_with("user@example.com")

    async def test_handle_password_reset_request_permission_error(self, controller):
        controller.service.initiate_password_reset.side_effect = PermissionError("rate limited")
        payload = PasswordResetInitiate(email="user@example.com")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_password_reset_request(payload)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_handle_password_reset_confirm_success(self, controller):
        controller.service.execute_password_reset.return_value = None
        payload = PasswordResetConfirm(token="token_abc", new_password="NewPass123!")
        result = await controller.handle_password_reset_confirm(payload)
        assert "updated successfully" in result["message"].lower()
        controller.service.execute_password_reset.assert_called_once_with(
            "token_abc", "NewPass123!"
        )

    async def test_handle_password_reset_confirm_permission_error(self, controller):
        controller.service.execute_password_reset.side_effect = PermissionError("invalid token")
        payload = PasswordResetConfirm(token="bad_token", new_password="NewPass123!")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_password_reset_confirm(payload)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_handle_password_reset_confirm_value_error(self, controller):
        controller.service.execute_password_reset.side_effect = ValueError("user missing")
        payload = PasswordResetConfirm(token="token_abc", new_password="NewPass123!")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_password_reset_confirm(payload)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
