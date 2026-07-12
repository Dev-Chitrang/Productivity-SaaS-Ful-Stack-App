import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.modules.auth.repository import AuthRepository


class TestAuthRepository:
    @pytest.fixture
    def repo(self):
        db = AsyncMock(spec=AsyncSession)
        return AuthRepository(db)

    async def test_get_by_email_active_only(self, repo):
        mock_user = User(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            email="user@example.com",
            password_hash="hash",
            full_name="User",
            is_active=True,
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_user
        repo.db.execute.return_value = result_mock

        user = await repo.get_by_email("user@example.com")
        assert user == mock_user
        repo.db.execute.assert_called_once()

    async def test_get_by_email_include_inactive(self, repo):
        mock_user = User(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            email="user@example.com",
            password_hash="hash",
            full_name="User",
            is_active=False,
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_user
        repo.db.execute.return_value = result_mock

        user = await repo.get_by_email("user@example.com", include_inactive=True)
        assert user == mock_user

    async def test_get_by_email_not_found(self, repo):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        repo.db.execute.return_value = result_mock

        user = await repo.get_by_email("missing@example.com")
        assert user is None

    async def test_get_by_google_id_found(self, repo):
        mock_user = User(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            email="oauth@example.com",
            password_hash=None,
            full_name="OAuth",
            is_active=True,
            google_id="google_123",
            oauth_provider="google",
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_user
        repo.db.execute.return_value = result_mock

        user = await repo.get_by_google_id("google_123")
        assert user == mock_user
        repo.db.execute.assert_called_once()

    async def test_get_by_google_id_not_found(self, repo):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        repo.db.execute.return_value = result_mock

        user = await repo.get_by_google_id("missing_google")
        assert user is None

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

    async def test_get_by_id_not_found(self, repo):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        repo.db.execute.return_value = result_mock

        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user = await repo.get_by_id(user_id)
        assert user is None

    async def test_create_success(self, repo):
        user = await repo.create(
            email="new@example.com",
            password_hash="hash",
            full_name="New User",
            is_2fa_enabled=False,
        )
        assert user.email == "new@example.com"
        assert user.password_hash == "hash"
        assert user.full_name == "New User"
        assert user.is_2fa_enabled is False
        repo.db.add.assert_called_once_with(user)

    async def test_create_oauth_success(self, repo):
        user = await repo.create_oauth_user(
            email="oauth_new@example.com",
            full_name="OAuth New",
            google_id="google_new",
            profile_image="https://example.com/pic.jpg",
        )
        assert user.email == "oauth_new@example.com"
        assert user.password_hash is None
        assert user.is_verified is True
        assert user.is_2fa_enabled is False
        assert user.google_id == "google_new"
        assert user.oauth_provider == "google"
        assert user.profile_image == "https://example.com/pic.jpg"
        repo.db.add.assert_called_once_with(user)

    async def test_create_oauth_no_profile_image(self, repo):
        user = await repo.create_oauth_user(
            email="oauth@example.com",
            full_name="OAuth",
            google_id="google_123",
        )
        assert user.profile_image is None

    async def test_link_google_account_new_link(self, repo, test_user):
        test_user.oauth_provider = None
        user = await repo.link_google_account(test_user, "google_new")
        assert user.google_id == "google_new"
        assert user.oauth_provider == "google+password"
        repo.db.add.assert_called_once_with(user)

    async def test_link_google_account_existing_other_provider(self, repo, test_user):
        test_user.oauth_provider = "other"
        user = await repo.link_google_account(test_user, "google_new")
        assert user.google_id == "google_new"
        assert user.oauth_provider == "other+google"
        repo.db.add.assert_called_once_with(user)

    async def test_link_google_account_preserves_existing_image(self, repo, test_user):
        test_user.profile_image = "https://existing.com/pic.jpg"
        user = await repo.link_google_account(
            test_user, "google_new", profile_image="https://new.com/pic.jpg"
        )
        assert user.profile_image == "https://existing.com/pic.jpg"
        repo.db.add.assert_called_once_with(user)

    async def test_link_google_account_sets_image_when_missing(self, repo, test_user):
        test_user.profile_image = None
        user = await repo.link_google_account(
            test_user, "google_new", profile_image="https://new.com/pic.jpg"
        )
        assert user.profile_image == "https://new.com/pic.jpg"

    async def test_update_password(self, repo, test_user):
        user = await repo.update_password(test_user, "new_hash")
        assert user.password_hash == "new_hash"
        repo.db.add.assert_called_once_with(user)

    async def test_mark_user_verified(self, repo, test_user):
        test_user.is_verified = False
        user = await repo.mark_user_verified(test_user)
        assert user.is_verified is True
        repo.db.add.assert_called_once_with(user)

    async def test_create_rollback_on_exception(self, repo):
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.create(
                email="fail@example.com",
                password_hash="hash",
                full_name="Fail",
            )
        repo.db.rollback.assert_called_once()

    async def test_create_oauth_rollback_on_exception(self, repo):
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.create_oauth_user(
                email="fail@example.com", full_name="Fail", google_id="g"
            )
        repo.db.rollback.assert_called_once()

    async def test_link_google_account_rollback_on_exception(self, repo, test_user):
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.link_google_account(test_user, "google_new")
        repo.db.rollback.assert_called_once()

    async def test_update_password_rollback_on_exception(self, repo, test_user):
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.update_password(test_user, "new_hash")
        repo.db.rollback.assert_called_once()

    async def test_mark_user_verified_rollback_on_exception(self, repo, test_user):
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.mark_user_verified(test_user)
        repo.db.rollback.assert_called_once()
