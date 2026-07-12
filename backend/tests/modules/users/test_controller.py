import uuid
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException, status
from app.modules.users.service import UserService
from app.modules.users.controller import UserController
from app.modules.users.schemas import (
    UpdateProfileRequest,
    ChangePasswordRequest,
    ChangeEmailRequest,
    ProfileImageRequest,
    Toggle2FARequest,
)


class TestUserController:
    @pytest.fixture
    def controller(self):
        service = MagicMock(spec=UserService)
        return UserController(service)

    async def test_handle_get_profile_success(self, controller):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user.email = "user@example.com"
        mock_user.full_name = "Test User"
        mock_user.is_verified = True
        mock_user.is_2fa_enabled = False
        mock_user.profile_image = None
        mock_user.timezone = "UTC"
        mock_user.created_at = "2024-01-01T00:00:00Z"
        controller.service.get_profile.return_value = mock_user

        result = await controller.handle_get_profile(str(mock_user.id))
        assert result["id"] == str(mock_user.id)
        assert result["email"] == "user@example.com"
        assert result["full_name"] == "Test User"
        assert result["is_verified"] is True
        assert result["is_2fa_enabled"] is False
        assert result["profile_image"] is None
        assert result["timezone"] == "UTC"
        assert result["created_at"] == "2024-01-01T00:00:00Z"

    async def test_handle_get_profile_user_not_found(self, controller):
        controller.service.get_profile.side_effect = ValueError("User not found.")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_get_profile("12345678-1234-5678-1234-567812345678")
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_handle_update_profile_success(self, controller):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user.email = "user@example.com"
        mock_user.full_name = "New Name"
        mock_user.is_verified = True
        mock_user.is_2fa_enabled = False
        mock_user.profile_image = None
        mock_user.timezone = "America/New_York"
        mock_user.created_at = "2024-01-01T00:00:00Z"
        controller.service.update_profile.return_value = mock_user

        payload = UpdateProfileRequest(full_name="New Name", timezone="America/New_York")
        result = await controller.handle_update_profile(str(mock_user.id), payload)
        assert result["full_name"] == "New Name"
        assert result["timezone"] == "America/New_York"

    async def test_handle_update_profile_user_not_found(self, controller):
        controller.service.update_profile.side_effect = ValueError("User not found.")
        payload = UpdateProfileRequest(full_name="New Name")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_update_profile("12345678-1234-5678-1234-567812345678", payload)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_handle_change_password_success(self, controller):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.change_password.return_value = None

        payload = ChangePasswordRequest(current_password="oldpass", new_password="newpass123")
        result = await controller.handle_change_password(str(mock_user.id), payload)
        assert "Password changed successfully" in result["message"]
        controller.service.change_password.assert_called_once_with(str(mock_user.id), "oldpass", "newpass123")

    async def test_handle_change_password_user_not_found(self, controller):
        controller.service.change_password.side_effect = ValueError("User not found.")
        payload = ChangePasswordRequest(current_password="oldpass", new_password="newpass123")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_change_password("12345678-1234-5678-1234-567812345678", payload)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_handle_change_password_wrong_current_password(self, controller):
        controller.service.change_password.side_effect = PermissionError("Current password is incorrect.")
        payload = ChangePasswordRequest(current_password="wrongpass", new_password="newpass123")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_change_password("12345678-1234-5678-1234-567812345678", payload)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_handle_change_email_success(self, controller):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.change_email.return_value = None

        payload = ChangeEmailRequest(current_password="oldpass", new_email="new@example.com")
        result = await controller.handle_change_email(str(mock_user.id), payload)
        assert "Email changed successfully" in result["message"]
        controller.service.change_email.assert_called_once_with(str(mock_user.id), "oldpass", "new@example.com")

    async def test_handle_change_email_user_not_found(self, controller):
        controller.service.change_email.side_effect = ValueError("User not found.")
        payload = ChangeEmailRequest(current_password="oldpass", new_email="new@example.com")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_change_email("12345678-1234-5678-1234-567812345678", payload)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_handle_change_email_wrong_password(self, controller):
        controller.service.change_email.side_effect = PermissionError("Current password is incorrect.")
        payload = ChangeEmailRequest(current_password="wrongpass", new_email="new@example.com")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_change_email("12345678-1234-5678-1234-567812345678", payload)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_handle_update_profile_image_success(self, controller):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user.profile_image = "base64data"
        controller.service.update_profile_image.return_value = mock_user

        payload = ProfileImageRequest(profile_image="base64data")
        result = await controller.handle_update_profile_image(str(mock_user.id), payload)
        assert result["message"] == "Profile image updated successfully."
        assert result["profile_image"] == "base64data"

    async def test_handle_update_profile_image_user_not_found(self, controller):
        controller.service.update_profile_image.side_effect = ValueError("User not found.")
        payload = ProfileImageRequest(profile_image="base64data")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_update_profile_image("12345678-1234-5678-1234-567812345678", payload)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_handle_toggle_2fa_enable_true(self, controller):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user.is_2fa_enabled = True
        controller.service.toggle_2fa.return_value = mock_user

        payload = Toggle2FARequest(enable=True)
        result = await controller.handle_toggle_2fa(str(mock_user.id), payload)
        assert result["message"] == "2FA settings updated."
        assert result["is_2fa_enabled"] is True

    async def test_handle_toggle_2fa_enable_false(self, controller):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user.is_2fa_enabled = False
        controller.service.toggle_2fa.return_value = mock_user

        payload = Toggle2FARequest(enable=False)
        result = await controller.handle_toggle_2fa(str(mock_user.id), payload)
        assert result["message"] == "2FA settings updated."
        assert result["is_2fa_enabled"] is False

    async def test_handle_toggle_2fa_user_not_found(self, controller):
        controller.service.toggle_2fa.side_effect = ValueError("User not found.")
        payload = Toggle2FARequest(enable=True)
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_toggle_2fa("12345678-1234-5678-1234-567812345678", payload)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_handle_deactivate_success(self, controller):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.deactivate_account.return_value = None

        result = await controller.handle_deactivate(str(mock_user.id))
        assert result["message"] == "Account successfully deactivated."
        controller.service.deactivate_account.assert_called_once_with(str(mock_user.id))

    async def test_handle_deactivate_user_not_found(self, controller):
        controller.service.deactivate_account.side_effect = ValueError("User not found.")
        with pytest.raises(HTTPException) as exc_info:
            await controller.handle_deactivate("12345678-1234-5678-1234-567812345678")
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_handle_change_password_logs_success(self, controller):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.change_password.return_value = None

        payload = ChangePasswordRequest(current_password="oldpass", new_password="newpass123")
        await controller.handle_change_password(str(mock_user.id), payload)
        controller.service.change_password.assert_called_once_with(str(mock_user.id), "oldpass", "newpass123")

    async def test_handle_change_email_logs_success(self, controller):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.change_email.return_value = None

        payload = ChangeEmailRequest(current_password="oldpass", new_email="new@example.com")
        await controller.handle_change_email(str(mock_user.id), payload)
        controller.service.change_email.assert_called_once_with(str(mock_user.id), "oldpass", "new@example.com")
