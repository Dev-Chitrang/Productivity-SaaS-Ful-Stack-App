from pydantic import BaseModel, EmailStr, Field, field_validator

class StrictEmailMixin:
    @field_validator("email")
    @classmethod
    def validate_real_domain(cls, value: str) -> str:
        email_clean = value.strip().lower()
        domain = email_clean.split("@")[-1]
        return email_clean

class UserRegisterRequest(BaseModel, StrictEmailMixin):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    enable_2fa: bool = False

class UserLoginRequest(BaseModel, StrictEmailMixin):
    email: EmailStr
    password: str

class OTPVerificationRequest(BaseModel):
    verification_token: str
    code: str = Field(..., min_length=6, max_length=6)

class ResendOtpRequest(BaseModel):
    verification_token: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class PasswordResetInitiate(BaseModel, StrictEmailMixin):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class SignupResponse(BaseModel):
    verification_token: str
    message: str

class LoginResponse(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"
    verification_token: str | None = None
    requires_2fa: bool = False

# --- Google OAuth ---

class GoogleOAuthRequest(BaseModel):
    """Payload sent from the frontend after completing Google's OAuth popup."""
    id_token: str = Field(..., description="Google ID Token obtained from the frontend OAuth flow.")

class GoogleOAuthResponse(BaseModel):
    """
    Returned on successful Google authentication.
    If 2FA is enabled the token fields are omitted and requires_2fa is True.
    """
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"
    requires_2fa: bool = False
    verification_token: str | None = None
