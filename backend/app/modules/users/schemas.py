from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_verified: bool
    is_2fa_enabled: bool
    profile_image: Optional[str] = None
    timezone: str
    created_at: datetime

    model_config = {"from_attributes": True}

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2)
    timezone: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class ChangeEmailRequest(BaseModel):
    current_password: str
    new_email: EmailStr

class ProfileImageRequest(BaseModel):
    profile_image: str

class Toggle2FARequest(BaseModel):
    enable: bool

class DeactivateAccountResponse(BaseModel):
    message: str
