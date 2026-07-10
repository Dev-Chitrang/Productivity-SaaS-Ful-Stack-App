import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.modules.users.repository import UserRepository


class TestUserRepository:
    @pytest.fixture
    def repo(self):
        db = AsyncMock(spec=AsyncSession)
        return UserRepository(db)

    async def test_get_by_id_found(self, repo):
        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user = User(
            id=user_id,
            email="user@example.com",
            password_hash="hash",
            full_name="User",
            is_active=True,
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_user
        repo.db.execute.return_value = result_mock

        user = await repo.get_by_id(user_id)
        assert user == mock_user
        repo.db.execute.assert_called_once()

    async def test_get_by_id_not_found(self, repo):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        repo.db.execute.return_value = result_mock

        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user = await repo.get_by_id(user_id)
        assert user is None

    async def test_update_profile_full_name_only(self, repo):
        user = User(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            email="user@example.com",
            password_hash="hash",
            full_name="Old Name",
            timezone="UTC",
        )
        result = await repo.update_profile(user, full_name="New Name")
        assert result.full_name == "New Name"
        assert result.timezone == "UTC"
        repo.db.add.assert_called_once_with(user)

    async def test_update_profile_timezone_only(self, repo):
        user = User(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            email="user@example.com",
            password_hash="hash",
            full_name="User",
            timezone="UTC",
        )
        result = await repo.update_profile(user, timezone="America/New_York")
        assert result.full_name == "User"
        assert result.timezone == "America/New_York"
        repo.db.add.assert_called_once_with(user)

    async def test_update_profile_both_fields(self, repo):
        user = User(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            email="user@example.com",
            password_hash="hash",
            full_name="Old Name",
            timezone="UTC",
        )
        result = await repo.update_profile(user, full_name="New Name", timezone="America/New_York")
        assert result.full_name == "New Name"
        assert result.timezone == "America/New_York"
        repo.db.add.assert_called_once_with(user)

    async def test_update_profile_no_changes(self, repo):
        user = User(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            email="user@example.com",
            password_hash="hash",
            full_name="User",
            timezone="UTC",
        )
        result = await repo.update_profile(user)
        assert result.full_name == "User"
        assert result.timezone == "UTC"
        repo.db.add.assert_called_once_with(user)

    async def test_update_profile_rollback_on_exception(self, repo):
        user = User(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            email="user@example.com",
            password_hash="hash",
            full_name="User",
            timezone="UTC",
        )
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.update_profile(user, full_name="New Name")
        repo.db.rollback.assert_called_once()

    async def test_update_email_success(self, repo):
        user = User(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            email="old@example.com",
            password_hash="hash",
            full_name="User",
        )
        result = await repo.update_email(user, "new@example.com")
        assert result.email == "new@example.com"
        repo.db.add.assert_called_once_with(user)

    async def test_update_email_rollback_on_exception(self, repo):
        user = User(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            email="old@example.com",
            password_hash="hash",
            full_name="User",
        )
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.update_email(user, "new@example.com")
        repo.db.rollback.assert_called_once()

    async def test_update_password_success(self, repo):
        user = User(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            email="user@example.com",
            password_hash="old_hash",
            full_name="User",
        )
        result = await repo.update_password(user, "new_hash")
        assert result.password_hash == "new_hash"
        repo.db.add.assert_called_once_with(user)

    async def test_update_password_rollback_on_exception(self, repo):
        user = User(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            email="user@example.com",
            password_hash="old_hash",
            full_name="User",
        )
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.update_password(user, "new_hash")
        repo.db.rollback.assert_called_once()

    async def test_update_profile_image_success(self, repo):
        user = User(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            email="user@example.com",
            password_hash="hash",
            full_name="User",
            profile_image=None,
        )
        result = await repo.update_profile_image(user, "base64_image_data")
        assert result.profile_image == "base64_image_data"
        repo.db.add.assert_called_once_with(user)

    async def test_update_profile_image_rollback_on_exception(self, repo):
        user = User(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            email="user@example.com",
            password_hash="hash",
            full_name="User",
            profile_image=None,
        )
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.update_profile_image(user, "base64_image_data")
        repo.db.rollback.assert_called_once()

    async def test_toggle_2fa_enable_true(self, repo):
        user = User(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            email="user@example.com",
            password_hash="hash",
            full_name="User",
            is_2fa_enabled=False,
        )
        result = await repo.toggle_2fa(user, True)
        assert result.is_2fa_enabled is True
        repo.db.add.assert_called_once_with(user)

    async def test_toggle_2fa_enable_false(self, repo):
        user = User(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            email="user@example.com",
            password_hash="hash",
            full_name="User",
            is_2fa_enabled=True,
        )
        result = await repo.toggle_2fa(user, False)
        assert result.is_2fa_enabled is False
        repo.db.add.assert_called_once_with(user)

    async def test_toggle_2fa_rollback_on_exception(self, repo):
        user = User(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            email="user@example.com",
            password_hash="hash",
            full_name="User",
            is_2fa_enabled=False,
        )
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.toggle_2fa(user, True)
        repo.db.rollback.assert_called_once()

    async def test_soft_delete_success(self, repo):
        user = User(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            email="user@example.com",
            password_hash="hash",
            full_name="User",
            is_active=True,
        )
        result = await repo.soft_delete(user)
        assert result is None
        assert user.is_active is False
        repo.db.add.assert_called_once_with(user)

    async def test_soft_delete_rollback_on_exception(self, repo):
        user = User(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            email="user@example.com",
            password_hash="hash",
            full_name="User",
            is_active=True,
        )
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.soft_delete(user)
        repo.db.rollback.assert_called_once()
