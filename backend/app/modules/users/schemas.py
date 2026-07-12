from zoneinfo import available_timezones

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime

_KNOWN_TIMEZONES = available_timezones()


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_verified: bool
    is_2fa_enabled: bool
    profile_image: Optional[str] = None
    # NULL means the user has not yet set a preference; the frontend will detect
    # the browser timezone and call PUT /users/profile to populate it.
    timezone: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2)
    timezone: Optional[str] = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if value not in _KNOWN_TIMEZONES:
            raise ValueError(
                f"'{value}' is not a valid IANA timezone identifier. "
                "Use a value from the IANA Time Zone Database (e.g. 'America/New_York', 'Europe/London')."
            )
        return value

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
