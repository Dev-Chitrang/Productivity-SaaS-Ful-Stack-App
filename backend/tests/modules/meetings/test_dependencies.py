import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.modules.meetings.dependencies import (
    get_current_user_id,
    get_optional_user_id,
    get_meetings_service,
)
from app.modules.meetings.service import MeetingService
from app.core.config import Settings


def _make_mock_settings():
    settings = MagicMock(spec=Settings)
    settings.JWT_SECRET_KEY = "test_secret"
    return settings


class TestGetCurrentUserId:
    async def test_valid_token_returns_uuid(self):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        token = jwt.encode({"sub": str(user_id)}, "test_secret", algorithm="HS256")
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with patch("app.modules.meetings.dependencies.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test_secret"
            result = get_current_user_id(creds)
        assert result == user_id

    async def test_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id(HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad_token"))
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_missing_sub_raises_401(self):
        token = jwt.encode({"foo": "bar"}, "test_secret", algorithm="HS256")
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with patch("app.modules.meetings.dependencies.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "wrong_secret"
            with pytest.raises(HTTPException) as exc_info:
                get_current_user_id(creds)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetOptionalUserId:
    async def test_valid_token_returns_uuid(self):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        token = jwt.encode({"sub": str(user_id)}, "test_secret", algorithm="HS256")
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with patch("app.modules.meetings.dependencies.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test_secret"
            result = get_optional_user_id(creds)
        assert result == user_id

    async def test_invalid_token_returns_none(self):
        with patch("app.modules.meetings.dependencies.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test_secret"
            result = get_optional_user_id(HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad_token"))
        assert result is None

    async def test_no_credentials_returns_none(self):
        with patch("app.modules.meetings.dependencies.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test_secret"
            result = get_optional_user_id(None)
        assert result is None


class TestGetMeetingsService:
    async def test_assembles_service(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_storage = MagicMock()
        with patch("app.modules.meetings.dependencies.get_db", return_value=mock_db), \
             patch("app.modules.meetings.dependencies.get_redis_client", return_value=mock_redis), \
             patch("app.modules.meetings.dependencies.get_meeting_storage", return_value=mock_storage):
            service = await get_meetings_service(mock_db, mock_storage, mock_redis)
        assert isinstance(service, MeetingService)
