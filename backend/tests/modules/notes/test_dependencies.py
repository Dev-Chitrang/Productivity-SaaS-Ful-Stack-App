import uuid
import jwt
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import Settings
from app.modules.notes.dependencies import (
    get_current_user_id,
    get_notes_service,
    security_scheme,
)
from app.modules.notes.services import NoteService


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


def _make_jwt(user_id: str, secret: str) -> str:
    return jwt.encode({"sub": user_id, "email": "user@example.com"}, secret, algorithm="HS256")


class TestGetCurrentUserId:
    async def test_valid_token_returns_uuid(self, mock_db):
        user_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        token = _make_jwt(user_id, "test_secret")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with patch("app.modules.notes.dependencies.get_db", return_value=mock_db), \
             patch("app.modules.notes.dependencies.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test_secret"
            result = get_current_user_id(credentials)
            assert result == uuid.UUID(user_id)

    async def test_invalid_token_raises_401(self, mock_db):
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")

        with patch("app.modules.notes.dependencies.get_db", return_value=mock_db), \
             patch("app.modules.notes.dependencies.settings") as mock_settings, \
             patch("app.modules.notes.dependencies.jwt.decode", side_effect=jwt.InvalidTokenError("bad token")):
            mock_settings.JWT_SECRET_KEY = "test_secret"
            with pytest.raises(HTTPException) as exc_info:
                get_current_user_id(credentials)
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_expired_token_raises_401(self, mock_db):
        old_token = _make_jwt("user_id", "test_secret")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=old_token)

        with patch("app.modules.notes.dependencies.get_db", return_value=mock_db), \
             patch("app.modules.notes.dependencies.settings") as mock_settings, \
             patch("app.modules.notes.dependencies.jwt.decode", side_effect=jwt.ExpiredSignatureError("expired")):
            mock_settings.JWT_SECRET_KEY = "test_secret"
            with pytest.raises(HTTPException) as exc_info:
                get_current_user_id(credentials)
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_missing_sub_claim_raises_key_error(self, mock_db):
        bad_token = jwt.encode({"email": "user@example.com"}, "test_secret", algorithm="HS256")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=bad_token)

        with patch("app.modules.notes.dependencies.get_db", return_value=mock_db), \
             patch("app.modules.notes.dependencies.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test_secret"
            with pytest.raises(KeyError):
                get_current_user_id(credentials)

    async def test_malformed_uuid_sub_raises_401(self, mock_db):
        bad_token = jwt.encode({"sub": "not-a-uuid"}, "test_secret", algorithm="HS256")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=bad_token)

        with patch("app.modules.notes.dependencies.get_db", return_value=mock_db), \
             patch("app.modules.notes.dependencies.settings") as mock_settings, \
             patch("app.modules.notes.dependencies.jwt.decode", return_value={"sub": "not-a-uuid"}):
            mock_settings.JWT_SECRET_KEY = "test_secret"
            with pytest.raises(HTTPException) as exc_info:
                get_current_user_id(credentials)
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestSecurityScheme:
    def test_security_scheme_is_http_bearer(self):
        assert isinstance(security_scheme, HTTPBearer)

    def test_security_scheme_default_scheme_name(self):
        assert security_scheme.scheme_name == "HTTPBearer"


class TestGetNotesService:
    async def test_returns_note_service(self, mock_db):
        with patch("app.modules.notes.dependencies.NoteRepository") as mock_repo_cls:
            mock_repo_cls.return_value = MagicMock()
            result = await get_notes_service(mock_db)
            assert isinstance(result, NoteService)

    async def test_repo_initialized_with_db(self, mock_db):
        with patch("app.modules.notes.dependencies.NoteRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo_cls.return_value = mock_repo
            result = await get_notes_service(mock_db)
            assert result.repo == mock_repo
            mock_repo_cls.assert_called_once_with(mock_db)
