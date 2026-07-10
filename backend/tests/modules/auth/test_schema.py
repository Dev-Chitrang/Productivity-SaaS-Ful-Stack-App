import pytest
from pydantic import ValidationError
from app.modules.auth.schema import (
    UserRegisterRequest,
    UserLoginRequest,
    OTPVerificationRequest,
    ResendOtpRequest,
    TokenRefreshRequest,
    PasswordResetInitiate,
    PasswordResetConfirm,
    TokenResponse,
    SignupResponse,
    LoginResponse,
    GoogleOAuthRequest,
    GoogleOAuthResponse,
)


class TestUserRegisterRequest:
    def test_valid_signup(self):
        data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "John Doe",
            "enable_2fa": False,
        }
        req = UserRegisterRequest(**data)
        assert req.email == "test@example.com"
        assert req.password == "SecurePass123!"
        assert req.full_name == "John Doe"
        assert req.enable_2fa is False

    def test_minimum_password_length(self):
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                email="test@example.com",
                password="short",
                full_name="John Doe",
            )

    def test_minimum_name_length(self):
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                email="test@example.com",
                password="SecurePass123!",
                full_name="J",
            )

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                email="invalid-email",
                password="SecurePass123!",
                full_name="John Doe",
            )

    def test_email_lowercased(self):
        req = UserRegisterRequest(
            email="  TEST@EXAMPLE.COM  ",
            password="SecurePass123!",
            full_name="John Doe",
        )
        assert req.email == "test@example.com"


class TestUserLoginRequest:
    def test_valid_login(self):
        req = UserLoginRequest(email="login@example.com", password="pass123")
        assert req.email == "login@example.com"
        assert req.password == "pass123"

    def test_email_is_lowercased(self):
        req = UserLoginRequest(email="  LOGIN@EXAMPLE.COM  ", password="pass123")
        assert req.email == "login@example.com"


class TestOTPVerificationRequest:
    def test_valid_otp(self):
        req = OTPVerificationRequest(verification_token="abc-123", code="123456")
        assert req.verification_token == "abc-123"
        assert req.code == "123456"

    def test_otp_must_be_six_digits(self):
        with pytest.raises(ValidationError):
            OTPVerificationRequest(verification_token="abc", code="123")


class TestResendOtpRequest:
    def test_valid(self):
        req = ResendOtpRequest(verification_token="token-xyz")
        assert req.verification_token == "token-xyz"


class TestTokenRefreshRequest:
    def test_valid(self):
        req = TokenRefreshRequest(refresh_token="refresh_abc")
        assert req.refresh_token == "refresh_abc"


class TestPasswordResetInitiate:
    def test_valid(self):
        req = PasswordResetInitiate(email="reset@example.com")
        assert req.email == "reset@example.com"

    def test_email_lowercased(self):
        req = PasswordResetInitiate(email="  RESET@EXAMPLE.COM  ")
        assert req.email == "reset@example.com"


class TestPasswordResetConfirm:
    def test_valid(self):
        req = PasswordResetConfirm(token="reset_token", new_password="NewPass123!")
        assert req.token == "reset_token"
        assert req.new_password == "NewPass123!"

    def test_minimum_new_password_length(self):
        with pytest.raises(ValidationError):
            PasswordResetConfirm(token="token", new_password="short")


class TestTokenResponse:
    def test_defaults(self):
        res = TokenResponse(access_token="acc", refresh_token="ref")
        assert res.access_token == "acc"
        assert res.refresh_token == "ref"
        assert res.token_type == "bearer"

    def test_custom_token_type(self):
        res = TokenResponse(access_token="acc", refresh_token="ref", token_type="custom")
        assert res.token_type == "custom"


class TestSignupResponse:
    def test_valid(self):
        res = SignupResponse(
            verification_token="vtok", message="Check your email."
        )
        assert res.verification_token == "vtok"
        assert res.message == "Check your email."


class TestLoginResponse:
    def test_defaults(self):
        res = LoginResponse()
        assert res.access_token is None
        assert res.refresh_token is None
        assert res.token_type == "bearer"
        assert res.requires_2fa is False

    def test_with_tokens(self):
        res = LoginResponse(
            access_token="acc", refresh_token="ref", requires_2fa=True
        )
        assert res.access_token == "acc"
        assert res.refresh_token == "ref"
        assert res.requires_2fa is True


class TestGoogleOAuthRequest:
    def test_valid(self):
        req = GoogleOAuthRequest(id_token="google_token")
        assert req.id_token == "google_token"

    def test_missing_id_token(self):
        with pytest.raises(ValidationError):
            GoogleOAuthRequest()


class TestGoogleOAuthResponse:
    def test_defaults(self):
        res = GoogleOAuthResponse()
        assert res.access_token is None
        assert res.refresh_token is None
        assert res.token_type == "bearer"
        assert res.requires_2fa is False

    def test_with_tokens_and_2fa(self):
        res = GoogleOAuthResponse(
            access_token="acc",
            refresh_token="ref",
            requires_2fa=True,
            verification_token="vtok",
        )
        assert res.requires_2fa is True
        assert res.verification_token == "vtok"
