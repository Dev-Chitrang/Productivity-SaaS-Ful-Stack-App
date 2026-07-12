import os
import pytest
from unittest.mock import patch
from pydantic import ValidationError

from app.core.config import (
    BaseAppSettings,
    LocalSettings,
    ProductionSettings,
    TestingSettings,
    Settings,
    _build_settings,
    _EnvironmentDetector,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NO_FILE = {"env_file": None, "extra": "ignore"}


def _no_env_file(cls):
    """Patch *cls*.model_config so it does not read from the .env file."""
    return patch.object(cls, "model_config", _NO_FILE)


_FULL_ENV = {
    "ENVIRONMENT": "LOCAL",
    "POSTGRES_SERVER": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_USER": "user",
    "POSTGRES_PASSWORD": "pass",
    "POSTGRES_DB": "db",
    "JWT_SECRET_KEY": "secret",
    "JWT_REFRESH_SECRET_KEY": "refresh_secret",
    "MEETING_SESSION_TOKEN_EXPIRE_MINUTES": "60",
    "REDIS_HOST": "localhost",
    "REDIS_PORT": "6379",
    "REDIS_CELERY_BROKER_URL": "redis://localhost:6379/0",
    "SMTP_HOST": "localhost",
    "SMTP_PORT": "587",
    "SMTP_USE_TLS": "true",
    "SMTP_FROM_EMAIL": "noreply@example.com",
    "GOOGLE_CLIENT_ID": "google_client_id",
    "FRONTEND_URL": "http://localhost:3000",
    "STORAGE_BASE_DIR": "/tmp/storage",
    "NVIDIA_NIM_API_KEY": "nim_key",
}


# ===================================================================
# LocalSettings
# ===================================================================

class TestLocalSettings:
    def test_required_fields_raises_when_missing(self):
        with patch.dict(os.environ, {}, clear=True), _no_env_file(LocalSettings):
            with pytest.raises(ValidationError):
                LocalSettings()

    def test_minimal_valid_config(self):
        with patch.dict(os.environ, _FULL_ENV, clear=True), _no_env_file(LocalSettings):
            s = LocalSettings()
            assert s.ENVIRONMENT == "LOCAL"
            assert s.POSTGRES_SERVER == "localhost"
            assert s.POSTGRES_PORT == 5432
            assert s.GOOGLE_CLIENT_ID == "google_client_id"

    def test_defaults(self):
        with patch.dict(os.environ, _FULL_ENV, clear=True), _no_env_file(LocalSettings):
            s = LocalSettings()
            assert s.NVIDIA_NIM_TIMEOUT == 300
            assert s.AWS_ACCESS_KEY_ID == ""
            assert s.AWS_SECRET_ACCESS_KEY == ""
            assert s.AWS_REGION == ""
            assert s.AWS_STORAGE_BUCKET_NAME == ""
            assert s.BREVO_API_KEY == ""
            assert s.BREVO_FROM_EMAIL == ""
            assert s.SMTP_USER is None
            assert s.SMTP_PASSWORD is None

    def test_async_database_url_property(self):
        env = {**_FULL_ENV, "POSTGRES_SERVER": "db.example.com", "POSTGRES_USER": "admin",
               "POSTGRES_PASSWORD": "secret", "POSTGRES_DB": "prod"}
        with patch.dict(os.environ, env, clear=True), _no_env_file(LocalSettings):
            s = LocalSettings()
            assert s.async_database_url == "postgresql+asyncpg://admin:secret@db.example.com:5432/prod"

    def test_storage_properties(self):
        env = {**_FULL_ENV, "STORAGE_BASE_DIR": "/data/storage"}
        with patch.dict(os.environ, env, clear=True), _no_env_file(LocalSettings):
            s = LocalSettings()
            assert s.meeting_storage == os.path.join("/data/storage", "meetings")
            assert s.transcribe_storage == os.path.join("/data/storage", "transcribe")
            assert s.attachment_storage == os.path.join("/data/storage", "attachments")

    def test_environment_validator_accepts_local(self):
        with patch.dict(os.environ, _FULL_ENV, clear=True), _no_env_file(LocalSettings):
            s = LocalSettings()
            assert s.ENVIRONMENT == "LOCAL"

    def test_environment_validator_rejects_invalid(self):
        env = {**_FULL_ENV, "ENVIRONMENT": "INVALID"}
        with patch.dict(os.environ, env, clear=True), _no_env_file(LocalSettings):
            with pytest.raises(ValidationError):
                LocalSettings()

    def test_smtp_port_can_be_integer(self):
        with patch.dict(os.environ, _FULL_ENV, clear=True), _no_env_file(LocalSettings):
            s = LocalSettings()
            assert s.SMTP_PORT == 587

    def test_extra_env_vars_ignored(self):
        env = {**_FULL_ENV, "UNKNOWN_FIELD": "should_be_ignored"}
        with patch.dict(os.environ, env, clear=True), _no_env_file(LocalSettings):
            s = LocalSettings()
            assert not hasattr(s, "UNKNOWN_FIELD")


# ===================================================================
# ProductionSettings
# ===================================================================

class TestProductionSettings:
    def test_required_fields_raises_when_missing(self):
        with patch.dict(os.environ, {}, clear=True), _no_env_file(ProductionSettings):
            with pytest.raises(ValidationError):
                ProductionSettings()

    def test_minimal_valid_config(self):
        env = {**_FULL_ENV, "ENVIRONMENT": "PRODUCTION"}
        with patch.dict(os.environ, env, clear=True), _no_env_file(ProductionSettings):
            s = ProductionSettings()
            assert s.ENVIRONMENT == "PRODUCTION"
            assert s.POSTGRES_SERVER == "localhost"

    def test_environment_validator_rejects_invalid(self):
        env = {**_FULL_ENV, "ENVIRONMENT": "INVALID"}
        with patch.dict(os.environ, env, clear=True), _no_env_file(ProductionSettings):
            with pytest.raises(ValidationError):
                ProductionSettings()


# ===================================================================
# TestingSettings
# ===================================================================

class TestTestingSettings:
    def test_can_be_created_with_no_env(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "TESTING"}, clear=True), \
             _no_env_file(TestingSettings):
            s = TestingSettings()
            assert s.ENVIRONMENT == "TESTING"

    def test_all_infra_defaults(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "TESTING"}, clear=True), \
             _no_env_file(TestingSettings):
            s = TestingSettings()
            assert s.POSTGRES_SERVER == "localhost"
            assert s.POSTGRES_PORT == 5432
            assert s.POSTGRES_USER == "test"
            assert s.REDIS_HOST == "localhost"
            assert s.REDIS_PORT == 6379
            assert s.SMTP_HOST == "localhost"
            assert s.GOOGLE_CLIENT_ID == "test-client-id"
            assert s.NVIDIA_NIM_API_KEY == "test-api-key"
            assert s.AWS_ACCESS_KEY_ID == ""
            assert s.BREVO_API_KEY == ""

    def test_jwt_defaults_are_safe_dummies(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "TESTING"}, clear=True), \
             _no_env_file(TestingSettings):
            s = TestingSettings()
            assert s.JWT_SECRET_KEY == "test-jwt-secret"
            assert s.JWT_REFRESH_SECRET_KEY == "test-jwt-refresh-secret"

    def test_async_database_url_uses_defaults(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "TESTING"}, clear=True), \
             _no_env_file(TestingSettings):
            s = TestingSettings()
            assert s.async_database_url == "postgresql+asyncpg://test:test@localhost:5432/test"

    def test_storage_properties_use_defaults(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "TESTING"}, clear=True), \
             _no_env_file(TestingSettings):
            s = TestingSettings()
            assert s.meeting_storage == os.path.join("/tmp/test-storage", "meetings")
            assert s.transcribe_storage == os.path.join("/tmp/test-storage", "transcribe")
            assert s.attachment_storage == os.path.join("/tmp/test-storage", "attachments")

    def test_env_vars_can_override_defaults(self):
        env = {"ENVIRONMENT": "TESTING", "POSTGRES_SERVER": "custom-host"}
        with patch.dict(os.environ, env, clear=True), _no_env_file(TestingSettings):
            s = TestingSettings()
            assert s.POSTGRES_SERVER == "custom-host"
            assert s.POSTGRES_PORT == 5432  # other fields keep defaults


# ===================================================================
# _build_settings factory
# ===================================================================

class TestBuildSettings:
    def test_returns_local_settings(self):
        env = {**_FULL_ENV, "ENVIRONMENT": "LOCAL"}
        with patch.dict(os.environ, env, clear=True), \
             _no_env_file(_EnvironmentDetector), \
             _no_env_file(LocalSettings):
            s = _build_settings()
            assert isinstance(s, LocalSettings)

    def test_returns_production_settings(self):
        env = {**_FULL_ENV, "ENVIRONMENT": "PRODUCTION"}
        with patch.dict(os.environ, env, clear=True), \
             _no_env_file(_EnvironmentDetector), \
             _no_env_file(ProductionSettings):
            s = _build_settings()
            assert isinstance(s, ProductionSettings)

    def test_returns_testing_settings(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "TESTING"}, clear=True), \
             _no_env_file(_EnvironmentDetector), \
             _no_env_file(TestingSettings):
            s = _build_settings()
            assert isinstance(s, TestingSettings)

    def test_rejects_invalid_environment(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "STAGING"}, clear=True), \
             _no_env_file(_EnvironmentDetector):
            with pytest.raises(ValueError, match="ENVIRONMENT must be one of"):
                _build_settings()

    def test_rejects_empty_environment(self):
        with patch.dict(os.environ, {}, clear=True), \
             _no_env_file(_EnvironmentDetector):
            with pytest.raises(ValueError, match="ENVIRONMENT must be one of"):
                _build_settings()


# ===================================================================
# Backward compatibility
# ===================================================================

class TestBackwardCompatibility:
    def test_settings_alias_is_local_settings(self):
        assert Settings is LocalSettings

    def test_settings_importable(self):
        from app.core.config import Settings as S
        assert S is LocalSettings
