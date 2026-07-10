import os
import pytest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError
from app.core.config import Settings


class TestSettings:
    def test_required_fields_raises_when_missing(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch("app.core.config.Settings.model_config", {"env_file": None, "extra": "ignore"}):
            with pytest.raises(ValidationError):
                Settings()

    def test_minimal_valid_config(self):
        env = {
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
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.ENVIRONMENT == "LOCAL"
            assert settings.POSTGRES_SERVER == "localhost"
            assert settings.POSTGRES_PORT == 5432
            assert settings.GOOGLE_CLIENT_ID == "google_client_id"

    def test_defaults(self):
        env = {
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
        with patch.dict(os.environ, env, clear=True), \
             patch("app.core.config.Settings.model_config", {"env_file": None, "extra": "ignore"}):
            settings = Settings()
            assert settings.ENVIRONMENT == "LOCAL"
            assert settings.NVIDIA_NIM_TIMEOUT == 300
            assert settings.AWS_ACCESS_KEY_ID == ""
            assert settings.AWS_SECRET_ACCESS_KEY == ""
            assert settings.AWS_REGION == ""
            assert settings.AWS_STORAGE_BUCKET_NAME == ""
            assert settings.BREVO_API_KEY == ""
            assert settings.BREVO_FROM_EMAIL == ""
            assert settings.SMTP_USER is None
            assert settings.SMTP_PASSWORD is None

    def test_async_database_url_property(self):
        env = {
            "ENVIRONMENT": "LOCAL",
            "POSTGRES_SERVER": "db.example.com",
            "POSTGRES_PORT": "5432",
            "POSTGRES_USER": "admin",
            "POSTGRES_PASSWORD": "secret",
            "POSTGRES_DB": "prod",
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
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            expected = "postgresql+asyncpg://admin:secret@db.example.com:5432/prod"
            assert settings.async_database_url == expected

    def test_storage_properties(self):
        env = {
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
            "STORAGE_BASE_DIR": "/data/storage",
            "NVIDIA_NIM_API_KEY": "nim_key",
        }
        with patch.dict(os.environ, env, clear=True), \
             patch("app.core.config.Settings.model_config", {"env_file": None, "extra": "ignore"}):
            settings = Settings()
            assert settings.meeting_storage == os.path.join("/data/storage", "meetings")
            assert settings.transcribe_storage == os.path.join("/data/storage", "transcribe")
            assert settings.attachment_storage == os.path.join("/data/storage", "attachments")

    def test_environment_validator_accepts_valid(self):
        env = {
            "ENVIRONMENT": "PRODUCTION",
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
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.ENVIRONMENT == "PRODUCTION"

    def test_environment_validator_rejects_invalid(self):
        env = {
            "ENVIRONMENT": "INVALID",
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
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    def test_smtp_port_can_be_integer(self):
        env = {
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
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.SMTP_PORT == 587

    def test_extra_env_vars_ignored(self):
        env = {
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
            "UNKNOWN_FIELD": "should_be_ignored",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert not hasattr(settings, "UNKNOWN_FIELD")
