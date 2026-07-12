import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.main import app
from app.core.database import get_db
from app.core.redis import get_redis_client
from app.modules.users.dependencies import get_current_user
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService
from app.modules.users.schemas import (
    UpdateProfileRequest,
    ChangePasswordRequest,
    ChangeEmailRequest,
    ProfileImageRequest,
    Toggle2FARequest,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_redis():
    mock = AsyncMock(spec=Redis)
    mock_pipeline = AsyncMock()
    mock_pipeline.zremrangebyscore = MagicMock()
    mock_pipeline.zcard = MagicMock()
    mock_pipeline.zrange = MagicMock()
    mock_pipeline.zadd = MagicMock()
    mock_pipeline.expire = MagicMock()
    mock_pipeline.execute = AsyncMock(return_value=[0, 0, []])
    mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
    mock_pipeline.__aexit__ = AsyncMock(return_value=False)
    mock.pipeline.return_value = mock_pipeline
    return mock


@pytest.fixture
def override_deps(mock_db, mock_redis):
    def _get_db():
        return mock_db

    def _get_redis():
        return mock_redis

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_redis_client] = _get_redis
    yield
    app.dependency_overrides.clear()


def _mock_current_user():
    mock_user = MagicMock()
    mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
    mock_user.email = "user@example.com"
    mock_user.full_name = "Test User"
    mock_user.is_verified = True
    mock_user.is_active = True
    mock_user.is_2fa_enabled = False
    mock_user.profile_image = None
    mock_user.timezone = "UTC"
    mock_user.created_at = "2024-01-01T00:00:00Z"
    return mock_user


class TestUserRoutes:
    async def test_get_profile_success(self, client, override_deps):
        mock_repo = MagicMock(spec=UserRepository)
        mock_service = MagicMock(spec=UserService)
        mock_user = _mock_current_user()
        mock_service.get_profile.return_value = mock_user

        app.dependency_overrides[get_current_user] = lambda: mock_user
        with patch(
            "app.modules.users.routes.UserRepository", return_value=mock_repo
        ), patch(
            "app.modules.users.routes.UserService", return_value=mock_service
        ):
            response = client.get("/api/v1/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "user@example.com"
        assert data["full_name"] == "Test User"

    async def test_get_profile_user_not_found(self, client, override_deps):
        mock_repo = MagicMock(spec=UserRepository)
        mock_service = MagicMock(spec=UserService)
        mock_service.get_profile.side_effect = ValueError("User not found.")

        app.dependency_overrides[get_current_user] = lambda: _mock_current_user()
        with patch(
            "app.modules.users.routes.UserRepository", return_value=mock_repo
        ), patch(
            "app.modules.users.routes.UserService", return_value=mock_service
        ):
            response = client.get("/api/v1/users/me")
        assert response.status_code == 404

    async def test_update_profile_success(self, client, override_deps):
        mock_repo = MagicMock(spec=UserRepository)
        mock_service = MagicMock(spec=UserService)
        mock_user = _mock_current_user()
        mock_user.full_name = "New Name"
        mock_service.update_profile.return_value = mock_user

        app.dependency_overrides[get_current_user] = lambda: mock_user
        with patch(
            "app.modules.users.routes.UserRepository", return_value=mock_repo
        ), patch(
            "app.modules.users.routes.UserService", return_value=mock_service
        ):
            response = client.put(
                "/api/v1/users/profile",
                json={"full_name": "New Name", "timezone": "America/New_York"},
            )
        assert response.status_code == 200
        assert response.json()["full_name"] == "New Name"

    async def test_update_profile_validation_error(self, client, override_deps):
        app.dependency_overrides[get_current_user] = lambda: _mock_current_user()
        response = client.put(
            "/api/v1/users/profile",
            json={"full_name": "A"},
        )
        assert response.status_code == 422

    async def test_change_password_success(self, client, override_deps):
        mock_repo = MagicMock(spec=UserRepository)
        mock_service = MagicMock(spec=UserService)
        mock_user = _mock_current_user()

        app.dependency_overrides[get_current_user] = lambda: mock_user
        with patch(
            "app.modules.users.routes.UserRepository", return_value=mock_repo
        ), patch(
            "app.modules.users.routes.UserService", return_value=mock_service
        ):
            response = client.put(
                "/api/v1/users/change-password",
                json={"current_password": "oldpass", "new_password": "newpass123"},
            )
        assert response.status_code == 200
        assert "Password changed successfully" in response.json()["message"]

    async def test_change_password_validation_error(self, client, override_deps):
        app.dependency_overrides[get_current_user] = lambda: _mock_current_user()
        response = client.put(
            "/api/v1/users/change-password",
            json={"current_password": "oldpass", "new_password": "short"},
        )
        assert response.status_code == 422

    async def test_change_email_success(self, client, override_deps):
        mock_repo = MagicMock(spec=UserRepository)
        mock_service = MagicMock(spec=UserService)
        mock_user = _mock_current_user()

        app.dependency_overrides[get_current_user] = lambda: mock_user
        with patch(
            "app.modules.users.routes.UserRepository", return_value=mock_repo
        ), patch(
            "app.modules.users.routes.UserService", return_value=mock_service
        ):
            response = client.put(
                "/api/v1/users/change-email",
                json={"current_password": "oldpass", "new_email": "new@example.com"},
            )
        assert response.status_code == 200
        assert "Email changed successfully" in response.json()["message"]

    async def test_change_email_validation_error(self, client, override_deps):
        app.dependency_overrides[get_current_user] = lambda: _mock_current_user()
        response = client.put(
            "/api/v1/users/change-email",
            json={"current_password": "oldpass", "new_email": "invalid-email"},
        )
        assert response.status_code == 422

    async def test_update_profile_image_success(self, client, override_deps):
        mock_repo = MagicMock(spec=UserRepository)
        mock_service = MagicMock(spec=UserService)
        mock_user = _mock_current_user()
        mock_user.profile_image = "base64data"
        mock_service.update_profile_image.return_value = mock_user

        app.dependency_overrides[get_current_user] = lambda: mock_user
        with patch(
            "app.modules.users.routes.UserRepository", return_value=mock_repo
        ), patch(
            "app.modules.users.routes.UserService", return_value=mock_service
        ):
            response = client.put(
                "/api/v1/users/profile-image",
                json={"profile_image": "base64data"},
            )
        assert response.status_code == 200
        assert response.json()["message"] == "Profile image updated successfully."

    async def test_toggle_2fa_success(self, client, override_deps):
        mock_repo = MagicMock(spec=UserRepository)
        mock_service = MagicMock(spec=UserService)
        mock_user = _mock_current_user()
        mock_user.is_2fa_enabled = True
        mock_service.toggle_2fa.return_value = mock_user

        app.dependency_overrides[get_current_user] = lambda: mock_user
        with patch(
            "app.modules.users.routes.UserRepository", return_value=mock_repo
        ), patch(
            "app.modules.users.routes.UserService", return_value=mock_service
        ):
            response = client.put(
                "/api/v1/users/2fa",
                json={"enable": True},
            )
        assert response.status_code == 200
        assert response.json()["message"] == "2FA settings updated."
        assert response.json()["is_2fa_enabled"] is True

    async def test_deactivate_success(self, client, override_deps):
        mock_repo = MagicMock(spec=UserRepository)
        mock_service = MagicMock(spec=UserService)
        mock_user = _mock_current_user()
        mock_service.deactivate_account.return_value = None

        app.dependency_overrides[get_current_user] = lambda: mock_user
        with patch(
            "app.modules.users.routes.UserRepository", return_value=mock_repo
        ), patch(
            "app.modules.users.routes.UserService", return_value=mock_service
        ):
            response = client.delete("/api/v1/users/deactivate")
        assert response.status_code == 200
        assert response.json()["message"] == "Account successfully deactivated."

    async def test_unauthorized_without_token(self, client, override_deps):
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401
