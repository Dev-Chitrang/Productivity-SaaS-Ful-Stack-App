from uuid import uuid4
from unittest.mock import patch, MagicMock
import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
import jwt

from app.modules.entity_links.dependencies import (
    get_current_user_id,
    get_entity_link_service,
)
from app.modules.entity_links.services import EntityLinkService


class TestGetCurrentUserId:
    def test_valid_token_returns_uuid(self):
        user_id = uuid4()
        token = jwt.encode({"sub": str(user_id)}, "test_secret", algorithm="HS256")
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with patch("app.modules.entity_links.dependencies.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test_secret"
            result = get_current_user_id(creds)
        assert result == user_id

    def test_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id(HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad_token"))
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials context signature" in str(exc_info.value.detail)

    def test_missing_sub_raises_key_error(self):
        token = jwt.encode({"foo": "bar"}, "test_secret", algorithm="HS256")
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with patch("app.modules.entity_links.dependencies.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test_secret"
            with pytest.raises(KeyError):
                get_current_user_id(creds)


class TestGetEntityLinkService:
    async def test_assembles_service(self):
        mock_db = MagicMock()
        mock_repo = MagicMock()
        with patch("app.modules.entity_links.dependencies.get_db", return_value=mock_db), \
             patch("app.modules.entity_links.dependencies.EntityLinkRepository", return_value=mock_repo):
            service = await get_entity_link_service(mock_db)
        assert isinstance(service, EntityLinkService)