import uuid
import jwt
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import Settings
from app.modules.users.dependencies import get_current_user, security_agent


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


def _make_jwt(user_id: str, secret: str) -> str:
    return jwt.encode({"sub": user_id, "email": "user@example.com"}, secret, algorithm="HS256")


class TestGetCurrentUser:
    async def test_valid_token_returns_user(self, mock_db):
        user_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        mock_user = MagicMock()
        mock_user.id = uuid.UUID(user_id)
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_user

        token = _make_jwt(user_id, "test_secret")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with patch("app.modules.users.dependencies.get_db", return_value=mock_db), \
             patch("app.modules.users.dependencies.settings") as mock_settings, \
             patch("app.modules.users.dependencies.UserRepository", return_value=mock_repo):
            mock_settings.JWT_SECRET_KEY = "test_secret"
            user = await get_current_user(credentials, mock_db)
            assert user == mock_user
            mock_repo.get_by_id.assert_called_once_with(uuid.UUID(user_id))

    async def test_invalid_token_raises_401(self, mock_db):
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")

        with patch("app.modules.users.dependencies.get_db", return_value=mock_db), \
             patch("app.modules.users.dependencies.settings") as mock_settings, \
             patch("app.modules.users.dependencies.jwt.decode", side_effect=jwt.InvalidTokenError("bad token")):
            mock_settings.JWT_SECRET_KEY = "test_secret"
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials, mock_db)
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert exc_info.value.detail == "Invalid token parameters."

    async def test_expired_token_raises_401(self, mock_db):
        old_token = _make_jwt("user_id", "test_secret")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=old_token)

        with patch("app.modules.users.dependencies.get_db", return_value=mock_db), \
             patch("app.modules.users.dependencies.settings") as mock_settings, \
             patch("app.modules.users.dependencies.jwt.decode", side_effect=jwt.ExpiredSignatureError("expired")):
            mock_settings.JWT_SECRET_KEY = "test_secret"
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials, mock_db)
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_user_not_found_raises_404(self, mock_db):
        user_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        token = _make_jwt(user_id, "test_secret")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        with patch("app.modules.users.dependencies.get_db", return_value=mock_db), \
             patch("app.modules.users.dependencies.settings") as mock_settings, \
             patch("app.modules.users.dependencies.UserRepository", return_value=mock_repo):
            mock_settings.JWT_SECRET_KEY = "test_secret"
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials, mock_db)
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert exc_info.value.detail == "User not found."

    async def test_missing_sub_claim_raises_key_error(self, mock_db):
        bad_token = jwt.encode({"email": "user@example.com"}, "test_secret", algorithm="HS256")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=bad_token)

        with patch("app.modules.users.dependencies.get_db", return_value=mock_db), \
             patch("app.modules.users.dependencies.settings") as mock_settings, \
             patch("app.modules.users.dependencies.UserRepository", return_value=AsyncMock()):
            mock_settings.JWT_SECRET_KEY = "test_secret"
            with pytest.raises(KeyError):
                await get_current_user(credentials, mock_db)


class TestSecurityAgent:
    def test_security_agent_is_http_bearer(self):
        assert isinstance(security_agent, HTTPBearer)

    def test_security_agent_default_scheme(self):
        assert security_agent.scheme_name == "HTTPBearer"
