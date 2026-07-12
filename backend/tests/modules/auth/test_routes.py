import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.main import app
from app.core.database import get_db
from app.core.redis import get_redis_client
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.modules.auth.controller import AuthController
from app.modules.auth.schema import (
    UserRegisterRequest,
    OTPVerificationRequest,
    UserLoginRequest,
    TokenRefreshRequest,
    PasswordResetInitiate,
    PasswordResetConfirm,
    ResendOtpRequest,
    GoogleOAuthRequest,
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


class TestAuthRoutes:
    async def test_signup_route_success(self, client, override_deps, mock_db, mock_redis):
        mock_repo = MagicMock(spec=AuthRepository)
        mock_repo.get_by_email.return_value = None
        mock_service = MagicMock(spec=AuthService)
        mock_service.register_user.return_value = "verification_token_abc"

        with patch(
            "app.modules.auth.routes.AuthRepository", return_value=mock_repo
        ), patch(
            "app.modules.auth.routes.AuthService", return_value=mock_service
        ):
            response = client.post(
                "/api/v1/auth/signup",
                json={
                    "email": "new@example.com",
                    "password": "SecurePass123!",
                    "full_name": "New User",
                },
            )
        assert response.status_code == 201
        assert response.json()["verification_token"] == "verification_token_abc"

    async def test_signup_route_duplicate_email(self, client, override_deps, mock_db, mock_redis):
        mock_repo = MagicMock(spec=AuthRepository)
        mock_repo.get_by_email.return_value = MagicMock()
        mock_service = MagicMock(spec=AuthService)
        mock_service.register_user.side_effect = ValueError("Identity profile already exists")

        with patch(
            "app.modules.auth.routes.AuthRepository", return_value=mock_repo
        ), patch(
            "app.modules.auth.routes.AuthService", return_value=mock_service
        ):
            response = client.post(
                "/api/v1/auth/signup",
                json={
                    "email": "existing@example.com",
                    "password": "SecurePass123!",
                    "full_name": "Existing",
                },
            )
        assert response.status_code == 400

    async def test_verify_signup_success(self, client, override_deps, mock_db, mock_redis):
        mock_service = MagicMock(spec=AuthService)
        mock_service.verify_registration_otp.return_value = {
            "access_token": "acc",
            "refresh_token": "ref",
        }

        with patch(
            "app.modules.auth.routes.AuthService", return_value=mock_service
        ):
            response = client.post(
                "/api/v1/auth/verify-signup",
                json={"verification_token": "vtok", "code": "123456"},
            )
        assert response.status_code == 200
        assert response.json()["access_token"] == "acc"

    async def test_resend_signup_otp_success(self, client, override_deps, mock_db, mock_redis):
        mock_service = MagicMock(spec=AuthService)
        mock_service.resend_signup_otp.return_value = None

        with patch(
            "app.modules.auth.routes.AuthService", return_value=mock_service
        ):
            response = client.post(
                "/api/v1/auth/resend-signup-otp",
                json={"verification_token": "vtok_abc"},
            )
        assert response.status_code == 200
        assert "resent" in response.json()["message"].lower()

    async def test_login_success(self, client, override_deps, mock_db, mock_redis):
        mock_service = MagicMock(spec=AuthService)
        mock_service.login_step_one.return_value = {
            "access_token": "acc",
            "refresh_token": "ref",
            "requires_2fa": False,
        }

        with patch(
            "app.modules.auth.routes.AuthService", return_value=mock_service
        ):
            response = client.post(
                "/api/v1/auth/login",
                json={"email": "user@example.com", "password": "password123"},
            )
        assert response.status_code == 200
        assert response.json()["access_token"] == "acc"

    async def test_login_wrong_password(self, client, override_deps, mock_db, mock_redis):
        mock_service = MagicMock(spec=AuthService)
        mock_service.login_step_one.side_effect = PermissionError("WRONG_PASSWORD")

        with patch(
            "app.modules.auth.routes.AuthService", return_value=mock_service
        ):
            response = client.post(
                "/api/v1/auth/login",
                json={"email": "user@example.com", "password": "wrong"},
            )
        assert response.status_code == 401

    async def test_verify_login_success(self, client, override_deps, mock_db, mock_redis):
        mock_service = MagicMock(spec=AuthService)
        mock_service.verify_login_otp.return_value = {
            "access_token": "acc",
            "refresh_token": "ref",
        }

        with patch(
            "app.modules.auth.routes.AuthService", return_value=mock_service
        ):
            response = client.post(
                "/api/v1/auth/verify-login",
                json={"verification_token": "vtok", "code": "123456"},
            )
        assert response.status_code == 200
        assert response.json()["access_token"] == "acc"

    async def test_resend_login_otp_success(self, client, override_deps, mock_db, mock_redis):
        mock_service = MagicMock(spec=AuthService)
        mock_service.resend_login_otp.return_value = None

        with patch(
            "app.modules.auth.routes.AuthService", return_value=mock_service
        ):
            response = client.post(
                "/api/v1/auth/resend-login-otp",
                json={"verification_token": "vtok"},
            )
        assert response.status_code == 200
        assert "resent" in response.json()["message"].lower()

    async def test_refresh_success(self, client, override_deps, mock_db, mock_redis):
        mock_service = MagicMock(spec=AuthService)
        mock_service.refresh_access_session.return_value = {
            "access_token": "new_acc",
            "refresh_token": "new_ref",
        }

        with patch(
            "app.modules.auth.routes.AuthService", return_value=mock_service
        ):
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "refresh_abc"},
            )
        assert response.status_code == 200
        assert response.json()["access_token"] == "new_acc"

    async def test_refresh_failure(self, client, override_deps, mock_db, mock_redis):
        mock_service = MagicMock(spec=AuthService)
        mock_service.refresh_access_session.side_effect = PermissionError("expired")

        with patch(
            "app.modules.auth.routes.AuthService", return_value=mock_service
        ):
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "expired_refresh"},
            )
        assert response.status_code == 401

    async def test_password_reset_initiate_success(self, client, override_deps, mock_db, mock_redis):
        mock_service = MagicMock(spec=AuthService)
        mock_service.initiate_password_reset.return_value = None

        with patch(
            "app.modules.auth.routes.AuthService", return_value=mock_service
        ):
            response = client.post(
                "/api/v1/auth/password-reset/initiate",
                json={"email": "user@example.com"},
            )
        assert response.status_code == 200
        assert "background initialized" in response.json()["message"].lower()

    async def test_password_reset_confirm_success(self, client, override_deps, mock_db, mock_redis):
        mock_service = MagicMock(spec=AuthService)
        mock_service.execute_password_reset.return_value = None

        with patch(
            "app.modules.auth.routes.AuthService", return_value=mock_service
        ):
            response = client.post(
                "/api/v1/auth/password-reset/confirm",
                json={"token": "reset_token", "new_password": "NewPass123!"},
            )
        assert response.status_code == 200
        assert "updated successfully" in response.json()["message"].lower()

    async def test_google_oauth_success(self, client, override_deps, mock_db, mock_redis):
        mock_service = MagicMock(spec=AuthService)
        mock_service.authenticate_with_google.return_value = {
            "access_token": "acc",
            "refresh_token": "ref",
            "requires_2fa": False,
        }

        with patch(
            "app.modules.auth.routes.AuthService", return_value=mock_service
        ):
            response = client.post(
                "/api/v1/auth/google",
                json={"id_token": "google_token_abc"},
            )
        assert response.status_code == 200
        assert response.json()["access_token"] == "acc"
