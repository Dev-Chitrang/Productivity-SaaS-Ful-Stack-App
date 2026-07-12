import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone


@pytest.fixture
def mock_db():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def sample_user_id():
    return uuid4()


@pytest.fixture
def sample_notification_id():
    return uuid4()


@pytest.fixture
def sample_subscription_data():
    return {
        "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint",
        "p256dh": "test-p256dh-key",
        "auth": "test-auth-key",
        "browser": "Chrome",
    }


@pytest.fixture
def sample_meeting_id():
    return uuid4()
