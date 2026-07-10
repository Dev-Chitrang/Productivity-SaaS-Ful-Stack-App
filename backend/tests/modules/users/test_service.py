import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.security import SecurityEngine
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService


class TestGetProfile:
    @pytest.fixture
    def service(self):
        repo = MagicMock(spec=UserRepository)
        redis = AsyncMock()
        return UserService(repo, redis)

    async def test_get_profile_success(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user.email = "user@example.com"
        service.repo.get_by_id.return_value = mock_user

        user = await service.get_profile(str(mock_user.id))
        assert user == mock_user
        service.repo.get_by_id.assert_called_once_with(mock_user.id)

    async def test_get_profile_user_not_found(self, service):
        service.repo.get_by_id.return_value = None
        with pytest.raises(ValueError, match="User not found."):
            await service.get_profile("12345678-1234-5678-1234-567812345678")
        service.repo.get_by_id.assert_called_once()


class TestUpdateProfile:
    @pytest.fixture
    def service(self):
        repo = MagicMock(spec=UserRepository)
        redis = AsyncMock()
        return UserService(repo, redis)

    async def test_update_profile_both_fields(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        service.repo.get_by_id.return_value = mock_user
        service.repo.update_profile.return_value = mock_user

        result = await service.update_profile(str(mock_user.id), full_name="New Name", timezone="America/New_York")
        service.repo.get_by_id.assert_called_once_with(mock_user.id)
        service.repo.update_profile.assert_called_once_with(mock_user, "New Name", "America/New_York")

    async def test_update_profile_full_name_only(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        service.repo.get_by_id.return_value = mock_user
        service.repo.update_profile.return_value = mock_user

        result = await service.update_profile(str(mock_user.id), full_name="New Name")
        service.repo.update_profile.assert_called_once_with(mock_user, "New Name", None)

    async def test_update_profile_timezone_only(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        service.repo.get_by_id.return_value = mock_user
        service.repo.update_profile.return_value = mock_user

        result = await service.update_profile(str(mock_user.id), timezone="America/New_York")
        service.repo.update_profile.assert_called_once_with(mock_user, None, "America/New_York")

    async def test_update_profile_no_changes(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        service.repo.get_by_id.return_value = mock_user
        service.repo.update_profile.return_value = mock_user

        result = await service.update_profile(str(mock_user.id))
        service.repo.update_profile.assert_called_once_with(mock_user, None, None)

    async def test_update_profile_user_not_found(self, service):
        service.repo.get_by_id.return_value = None
        with pytest.raises(ValueError, match="User not found."):
            await service.update_profile("12345678-1234-5678-1234-567812345678")


class TestChangePassword:
    @pytest.fixture
    def service(self):
        repo = MagicMock(spec=UserRepository)
        redis = AsyncMock()
        return UserService(repo, redis)

    async def test_change_password_success(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user.password_hash = "hashed_old"
        service.repo.get_by_id.return_value = mock_user

        with patch.object(SecurityEngine, "verify_password", return_value=True), patch.object(
            SecurityEngine, "hash_password", return_value="hashed_new"
        ):
            await service.change_password(str(mock_user.id), "oldpassword", "newpassword")
            service.repo.update_password.assert_called_once_with(mock_user, "hashed_new")
            service.redis.delete.assert_called_once_with(f"session:{mock_user.id}")

    async def test_change_password_user_not_found(self, service):
        service.repo.get_by_id.return_value = None
        with pytest.raises(ValueError, match="User not found."):
            await service.change_password("12345678-1234-5678-1234-567812345678", "oldpassword", "newpassword")

    async def test_change_password_wrong_current_password(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user.password_hash = "hashed_old"
        service.repo.get_by_id.return_value = mock_user

        with patch.object(SecurityEngine, "verify_password", return_value=False):
            with pytest.raises(PermissionError, match="Current password is incorrect."):
                await service.change_password(str(mock_user.id), "wrongpassword", "newpassword")
            service.repo.update_password.assert_not_called()

    async def test_change_password_deletes_redis_session(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user.password_hash = "hashed_old"
        service.repo.get_by_id.return_value = mock_user

        with patch.object(SecurityEngine, "verify_password", return_value=True), patch.object(
            SecurityEngine, "hash_password", return_value="hashed_new"
        ):
            await service.change_password(str(mock_user.id), "oldpassword", "newpassword")
            service.redis.delete.assert_called_once_with(f"session:{mock_user.id}")


class TestChangeEmail:
    @pytest.fixture
    def service(self):
        repo = MagicMock(spec=UserRepository)
        redis = AsyncMock()
        return UserService(repo, redis)

    async def test_change_email_success(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user.email = "old@example.com"
        service.repo.get_by_id.return_value = mock_user

        with patch.object(SecurityEngine, "verify_password", return_value=True):
            await service.change_email(str(mock_user.id), "oldpassword", "new@example.com")
            service.repo.update_email.assert_called_once_with(mock_user, "new@example.com")
            service.redis.delete.assert_called_once_with(f"session:{mock_user.id}")

    async def test_change_email_user_not_found(self, service):
        service.repo.get_by_id.return_value = None
        with pytest.raises(ValueError, match="User not found."):
            await service.change_email("12345678-1234-5678-1234-567812345678", "oldpassword", "new@example.com")

    async def test_change_email_wrong_password(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        service.repo.get_by_id.return_value = mock_user

        with patch.object(SecurityEngine, "verify_password", return_value=False):
            with pytest.raises(PermissionError, match="Current password is incorrect."):
                await service.change_email(str(mock_user.id), "wrongpassword", "new@example.com")
            service.repo.update_email.assert_not_called()

    async def test_change_email_deletes_redis_session(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user.email = "old@example.com"
        service.repo.get_by_id.return_value = mock_user

        with patch.object(SecurityEngine, "verify_password", return_value=True):
            await service.change_email(str(mock_user.id), "oldpassword", "new@example.com")
            service.redis.delete.assert_called_once_with(f"session:{mock_user.id}")


class TestUpdateProfileImage:
    @pytest.fixture
    def service(self):
        repo = MagicMock(spec=UserRepository)
        redis = AsyncMock()
        return UserService(repo, redis)

    async def test_update_profile_image_success(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user.profile_image = None
        service.repo.get_by_id.return_value = mock_user
        service.repo.update_profile_image.return_value = mock_user

        result = await service.update_profile_image(str(mock_user.id), "base64data")
        service.repo.update_profile_image.assert_called_once_with(mock_user, "base64data")
        assert result == mock_user

    async def test_update_profile_image_user_not_found(self, service):
        service.repo.get_by_id.return_value = None
        with pytest.raises(ValueError, match="User not found."):
            await service.update_profile_image("12345678-1234-5678-1234-567812345678", "base64data")


class TestToggle2FA:
    @pytest.fixture
    def service(self):
        repo = MagicMock(spec=UserRepository)
        redis = AsyncMock()
        return UserService(repo, redis)

    async def test_toggle_2fa_enable_true(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user.is_2fa_enabled = False
        service.repo.get_by_id.return_value = mock_user
        service.repo.toggle_2fa.return_value = mock_user

        result = await service.toggle_2fa(str(mock_user.id), True)
        service.repo.toggle_2fa.assert_called_once_with(mock_user, True)
        assert result == mock_user

    async def test_toggle_2fa_enable_false(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user.is_2fa_enabled = True
        service.repo.get_by_id.return_value = mock_user
        service.repo.toggle_2fa.return_value = mock_user

        result = await service.toggle_2fa(str(mock_user.id), False)
        service.repo.toggle_2fa.assert_called_once_with(mock_user, False)
        assert result == mock_user

    async def test_toggle_2fa_user_not_found(self, service):
        service.repo.get_by_id.return_value = None
        with pytest.raises(ValueError, match="User not found."):
            await service.toggle_2fa("12345678-1234-5678-1234-567812345678", True)


class TestDeactivateAccount:
    @pytest.fixture
    def service(self):
        repo = MagicMock(spec=UserRepository)
        redis = AsyncMock()
        return UserService(repo, redis)

    async def test_deactivate_account_success(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        service.repo.get_by_id.return_value = mock_user

        await service.deactivate_account(str(mock_user.id))
        service.repo.soft_delete.assert_called_once_with(mock_user)
        service.redis.delete.assert_called_once_with(f"session:{mock_user.id}")

    async def test_deactivate_account_user_not_found(self, service):
        service.repo.get_by_id.return_value = None
        with pytest.raises(ValueError, match="User not found."):
            await service.deactivate_account("12345678-1234-5678-1234-567812345678")
        service.repo.soft_delete.assert_not_called()

    async def test_deactivate_account_deletes_redis_session(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        service.repo.get_by_id.return_value = mock_user

        await service.deactivate_account(str(mock_user.id))
        service.redis.delete.assert_called_once_with(f"session:{mock_user.id}")
