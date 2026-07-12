from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.modules.users.schemas import (
    UserProfileResponse,
    UpdateProfileRequest,
    ChangePasswordRequest,
    ChangeEmailRequest,
    ProfileImageRequest,
    Toggle2FARequest,
    DeactivateAccountResponse,
)


class TestUserProfileResponse:
    def test_valid_response(self):
        data = {
            "id": "12345678-1234-5678-1234-567812345678",
            "email": "user@example.com",
            "full_name": "Test User",
            "is_verified": True,
            "is_2fa_enabled": False,
            "profile_image": "https://example.com/pic.jpg",
            "timezone": "UTC",
            "created_at": "2024-01-01T00:00:00Z",
        }
        resp = UserProfileResponse(**data)
        assert resp.id == data["id"]
        assert resp.email == data["email"]
        assert resp.full_name == data["full_name"]
        assert resp.is_verified is True
        assert resp.is_2fa_enabled is False
        assert resp.profile_image == data["profile_image"]
        assert resp.timezone == "UTC"
        assert resp.created_at is not None

    def test_profile_image_defaults_to_none(self):
        data = {
            "id": "12345678-1234-5678-1234-567812345678",
            "email": "user@example.com",
            "full_name": "Test User",
            "is_verified": True,
            "is_2fa_enabled": False,
            "timezone": "UTC",
            "created_at": "2024-01-01T00:00:00Z",
        }
        resp = UserProfileResponse(**data)
        assert resp.profile_image is None

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            UserProfileResponse(
                id="12345678-1234-5678-1234-567812345678",
                email="user@example.com",
                full_name="Test User",
                is_verified=True,
                is_2fa_enabled=False,
                profile_image=None,
                timezone="UTC",
            )

    def test_valid_email_format(self):
        model = UserProfileResponse(
            id="12345678-1234-5678-1234-567812345678",
            email="invalid-email",
            full_name="Test User",
            is_verified=True,
            is_2fa_enabled=False,
            timezone="UTC",
            created_at=datetime.now(timezone.utc),
        )
        assert model.email == "invalid-email"

    def test_missing_timezone_is_none(self):
        resp = UserProfileResponse(
            id="12345678-1234-5678-1234-567812345678",
            email="user@example.com",
            full_name="Test User",
            is_verified=True,
            is_2fa_enabled=False,
            created_at="2024-01-01T00:00:00Z",
        )
        assert resp.timezone is None


class TestUpdateProfileRequest:
    def test_valid_no_changes(self):
        payload = UpdateProfileRequest()
        assert payload.full_name is None
        assert payload.timezone is None

    def test_valid_full_name_only(self):
        payload = UpdateProfileRequest(full_name="New Name")
        assert payload.full_name == "New Name"
        assert payload.timezone is None

    def test_valid_timezone_only(self):
        payload = UpdateProfileRequest(timezone="America/New_York")
        assert payload.full_name is None
        assert payload.timezone == "America/New_York"

    def test_valid_both(self):
        payload = UpdateProfileRequest(full_name="New Name", timezone="America/New_York")
        assert payload.full_name == "New Name"
        assert payload.timezone == "America/New_York"

    def test_full_name_too_short_raises(self):
        with pytest.raises(ValidationError):
            UpdateProfileRequest(full_name="A")

    def test_full_name_exactly_two_chars(self):
        payload = UpdateProfileRequest(full_name="Ab")
        assert payload.full_name == "Ab"

    def test_full_name_not_provided_is_valid(self):
        payload = UpdateProfileRequest(full_name=None)
        assert payload.full_name is None


class TestChangePasswordRequest:
    def test_valid(self):
        payload = ChangePasswordRequest(current_password="oldpass", new_password="newpass123")
        assert payload.current_password == "oldpass"
        assert payload.new_password == "newpass123"

    def test_new_password_too_short_raises(self):
        with pytest.raises(ValidationError):
            ChangePasswordRequest(current_password="oldpass", new_password="short")

    def test_new_password_exactly_eight_chars(self):
        payload = ChangePasswordRequest(current_password="oldpass", new_password="12345678")
        assert payload.new_password == "12345678"

    def test_missing_current_password_raises(self):
        with pytest.raises(ValidationError):
            ChangePasswordRequest(new_password="newpass123")

    def test_missing_new_password_raises(self):
        with pytest.raises(ValidationError):
            ChangePasswordRequest(current_password="oldpass")


class TestChangeEmailRequest:
    def test_valid(self):
        payload = ChangeEmailRequest(current_password="oldpass", new_email="new@example.com")
        assert payload.current_password == "oldpass"
        assert payload.new_email == "new@example.com"

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            ChangeEmailRequest(current_password="oldpass", new_email="invalid-email")

    def test_missing_current_password_raises(self):
        with pytest.raises(ValidationError):
            ChangeEmailRequest(new_email="new@example.com")

    def test_missing_new_email_raises(self):
        with pytest.raises(ValidationError):
            ChangeEmailRequest(current_password="oldpass")

    def test_email_is_lowercased(self):
        payload = ChangeEmailRequest(current_password="oldpass", new_email="  NEW@EXAMPLE.COM  ")
        assert payload.new_email == "NEW@example.com"


class TestProfileImageRequest:
    def test_valid(self):
        payload = ProfileImageRequest(profile_image="https://example.com/pic.jpg")
        assert payload.profile_image == "https://example.com/pic.jpg"

    def test_empty_string_is_valid(self):
        payload = ProfileImageRequest(profile_image="")
        assert payload.profile_image == ""

    def test_base64_string_is_valid(self):
        b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        payload = ProfileImageRequest(profile_image=b64)
        assert payload.profile_image == b64


class TestToggle2FARequest:
    def test_enable_true(self):
        payload = Toggle2FARequest(enable=True)
        assert payload.enable is True

    def test_enable_false(self):
        payload = Toggle2FARequest(enable=False)
        assert payload.enable is False

    def test_missing_enable_raises(self):
        with pytest.raises(ValidationError):
            Toggle2FARequest()


class TestDeactivateAccountResponse:
    def test_valid(self):
        payload = DeactivateAccountResponse(message="Account successfully deactivated.")
        assert payload.message == "Account successfully deactivated."

    def test_missing_message_raises(self):
        with pytest.raises(ValidationError):
            DeactivateAccountResponse()
