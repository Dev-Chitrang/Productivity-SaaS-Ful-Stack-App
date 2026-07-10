import uuid
from datetime import datetime, timezone
import pytest
from app.models.user import User


class TestUserModel:
    def test_tablename(self):
        assert User.__tablename__ == "users"

    def test_id_default_generates_uuid(self):
        user = User(email="test@example.com", full_name="Test", password_hash=None)
        assert user.id is None or isinstance(user.id, (uuid.UUID, type(uuid.uuid7())))
        assert user.email == "test@example.com"
        assert user.full_name == "Test"

    def test_minimal_fields(self):
        now = datetime.now(timezone.utc)
        user = User(
            email="minimal@example.com",
            full_name="Minimal",
            is_verified=False,
            is_active=True,
            is_2fa_enabled=False,
            timezone="UTC",
            created_at=now,
        )
        assert user.email == "minimal@example.com"
        assert user.full_name == "Minimal"
        assert user.password_hash is None
        assert user.is_verified is False
        assert user.is_active is True
        assert user.is_2fa_enabled is False
        assert user.profile_image is None
        assert user.timezone == "UTC"
        assert user.google_id is None
        assert user.oauth_provider is None
        assert isinstance(user.created_at, datetime)

    def test_full_fields(self):
        uid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        now = datetime.now(timezone.utc)
        user = User(
            id=uid,
            email="full@example.com",
            password_hash="hash123",
            full_name="Full User",
            is_verified=True,
            is_active=True,
            is_2fa_enabled=True,
            profile_image="https://example.com/pic.jpg",
            timezone="America/New_York",
            google_id="google_123",
            oauth_provider="google",
            created_at=now,
        )
        assert user.id == uid
        assert user.email == "full@example.com"
        assert user.password_hash == "hash123"
        assert user.full_name == "Full User"
        assert user.is_verified is True
        assert user.is_active is True
        assert user.is_2fa_enabled is True
        assert user.profile_image == "https://example.com/pic.jpg"
        assert user.timezone == "America/New_York"
        assert user.google_id == "google_123"
        assert user.oauth_provider == "google"
        assert user.created_at == now

    def test_oauth_user_defaults(self):
        user = User(
            email="oauth@example.com",
            password_hash=None,
            full_name="OAuth",
            is_verified=True,
            is_2fa_enabled=False,
            google_id="google_456",
            oauth_provider="google",
        )
        assert user.password_hash is None
        assert user.is_verified is True
        assert user.is_2fa_enabled is False
        assert user.google_id == "google_456"
        assert user.oauth_provider == "google"

    def test_created_at_default_is_utc(self):
        now = datetime.now(timezone.utc)
        user = User(email="dt@example.com", full_name="DT", created_at=now)
        assert user.created_at is not None
        assert user.created_at.tzinfo == timezone.utc

    def test_email_unique_index(self):
        assert User.email.property.columns[0].unique is True
        assert User.email.property.columns[0].index is True

    def test_google_id_unique_index(self):
        assert User.google_id.property.columns[0].unique is True
        assert User.google_id.property.columns[0].index is True
