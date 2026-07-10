import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.security import SecurityEngine
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.modules.auth.controller import AuthController


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_redis():
    return AsyncMock()


@pytest.fixture
def mock_repo(mock_db):
    return AuthRepository(mock_db)


@pytest.fixture
def mock_security():
    s = MagicMock(spec=SecurityEngine)
    s.hash_password.return_value = "hashed_pw_123"
    s.verify_password.return_value = True
    s.generate_auth_tokens.return_value = {
        "access_token": "access_123",
        "refresh_token": "refresh_123",
        "token_type": "bearer",
    }
    return s


@pytest.fixture
def mock_service(mock_repo, mock_redis):
    return AuthService(mock_repo, mock_redis)


@pytest.fixture
def mock_controller(mock_service):
    return AuthController(mock_service)


@pytest.fixture
def test_user():
    return User(
        id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        email="test@example.com",
        password_hash="hashed_pw",
        full_name="Test User",
        is_verified=True,
        is_active=True,
        is_2fa_enabled=False,
        oauth_provider=None,
        google_id=None,
        profile_image=None,
    )


@pytest.fixture
def oauth_user():
    return User(
        id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
        email="oauth@example.com",
        password_hash=None,
        full_name="OAuth User",
        is_verified=True,
        is_active=True,
        is_2fa_enabled=False,
        oauth_provider="google",
        google_id="google_123",
        profile_image="https://example.com/pic.jpg",
    )
