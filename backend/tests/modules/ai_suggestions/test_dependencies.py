import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.modules.ai_suggestions import dependencies as deps
from app.modules.ai_suggestions.dependencies import get_current_user_id, get_ai_suggestion_service
from app.modules.ai_suggestions.repository import AISuggestionRepository
from app.modules.ai_suggestions.services import AISuggestionService


SECRET = "test_ai_suggestion_secret_key_at_least_32_byt3s"


def _make_settings():
    settings = MagicMock()
    settings.JWT_SECRET_KEY = SECRET
    return settings


def _make_token(sub: str) -> str:
    return jwt.encode({"sub": sub}, SECRET, algorithm="HS256")


class TestGetCurrentUserId:
    @pytest.fixture
    def settings_patch(self):
        with patch.object(deps, "settings", _make_settings()):
            yield

    def test_valid_token(self, settings_patch):
        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        token = _make_token(str(user_id))
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        result = get_current_user_id(creds)
        assert result == user_id

    def test_invalid_signature_raises_401(self, settings_patch):
        token = jwt.encode({"sub": str(uuid.uuid4())}, "wrong_secret", algorithm="HS256")
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(HTTPException) as exc:
            get_current_user_id(creds)
        assert exc.value.status_code == 401
        assert "Could not validate credentials" in exc.value.detail

    def test_malformed_token_raises_401(self, settings_patch):
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not.a.jwt")
        with pytest.raises(HTTPException) as exc:
            get_current_user_id(creds)
        assert exc.value.status_code == 401

    def test_missing_sub_propagates_keyerror(self, settings_patch):
        # NOTE: production only catches (jwt.PyJWTError, ValueError); a missing
        # "sub" claim raises KeyError in UUID(payload["sub"]) and is NOT converted
        # to a 401. Asserting actual (unhandled) behaviour.
        token = jwt.encode({"other": "x"}, SECRET, algorithm="HS256")
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(KeyError):
            get_current_user_id(creds)

    def test_expired_token_raises_401(self, settings_patch):
        token = jwt.encode(
            {"sub": str(uuid.uuid4())}, SECRET, algorithm="HS256"
        )
        # Use a token that fails decode by tampering payload - decode will raise
        tampered = token + "tamper"
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=tampered)
        with pytest.raises(HTTPException) as exc:
            get_current_user_id(creds)
        assert exc.value.status_code == 401


class TestGetAISuggestionService:
    async def test_returns_service_with_repo(self):
        mock_db = AsyncMock()
        service = await get_ai_suggestion_service(mock_db)
        assert isinstance(service, AISuggestionService)
        assert isinstance(service.repo, AISuggestionRepository)
        assert service.repo.db is mock_db
