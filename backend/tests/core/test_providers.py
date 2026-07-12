import pytest
from unittest.mock import patch, MagicMock
from app.core.providers import get_storage_provider, get_storage_service, get_email_provider
from app.core.config import Settings


class TestGetStorageProvider:
    def test_local_storage_when_not_production(self):
        settings = MagicMock(spec=Settings)
        settings.ENVIRONMENT = "LOCAL"
        settings.STORAGE_BASE_DIR = "/tmp/storage"

        with patch("app.core.providers.settings", settings):
            provider = get_storage_provider()
            assert provider is not None
            assert hasattr(provider, "save")

    def test_local_storage_with_subdir(self):
        settings = MagicMock(spec=Settings)
        settings.ENVIRONMENT = "LOCAL"
        settings.STORAGE_BASE_DIR = "/tmp/storage"

        with patch("app.core.providers.settings", settings):
            provider = get_storage_provider("meetings")
            assert provider is not None

    def test_s3_storage_when_production(self):
        settings = MagicMock(spec=Settings)
        settings.ENVIRONMENT = "PRODUCTION"
        settings.STORAGE_BASE_DIR = "/tmp/storage"

        with patch("app.core.providers.settings", settings):
            with patch("app.core.providers.S3StorageProvider") as mock_s3:
                mock_s3.return_value = MagicMock()
                provider = get_storage_provider()
                mock_s3.assert_called_once()


class TestGetStorageService:
    def test_returns_storage_service(self):
        with patch("app.core.providers.get_storage_provider") as mock_provider_fn:
            mock_provider = MagicMock()
            mock_provider_fn.return_value = mock_provider
            service = get_storage_service("meetings")
            assert service is not None
            assert hasattr(service, "save_recording")

    def test_passes_subdir_to_provider(self):
        with patch("app.core.providers.get_storage_provider") as mock_provider_fn:
            mock_provider = MagicMock()
            mock_provider_fn.return_value = mock_provider
            service = get_storage_service("transcribe")
            mock_provider_fn.assert_called_once_with("transcribe")


class TestGetEmailProvider:
    def test_local_environment_returns_smtp(self):
        settings = MagicMock(spec=Settings)
        settings.ENVIRONMENT = "LOCAL"
        settings.SMTP_HOST = "localhost"
        settings.SMTP_PORT = 587
        settings.SMTP_USE_TLS = True
        settings.SMTP_USER = None
        settings.SMTP_PASSWORD = None
        settings.SMTP_FROM_EMAIL = "noreply@example.com"
        settings.BREVO_API_KEY = ""
        settings.BREVO_FROM_EMAIL = ""

        with patch("app.core.providers.settings", settings):
            provider = get_email_provider()
            assert provider is not None
            from app.core.email import SMTPEmailProvider
            assert isinstance(provider, SMTPEmailProvider)

    def test_production_environment_returns_brevo(self):
        settings = MagicMock(spec=Settings)
        settings.ENVIRONMENT = "PRODUCTION"
        settings.SMTP_HOST = "localhost"
        settings.SMTP_PORT = 587
        settings.SMTP_USE_TLS = True
        settings.SMTP_USER = None
        settings.SMTP_PASSWORD = None
        settings.SMTP_FROM_EMAIL = "noreply@example.com"
        settings.BREVO_API_KEY = "brevo_key"
        settings.BREVO_FROM_EMAIL = "brevo@example.com"

        with patch("app.core.providers.settings", settings):
            with patch("app.core.email.BrevoEmailProvider") as mock_brevo:
                mock_brevo.return_value = MagicMock()
                provider = get_email_provider()
                mock_brevo.assert_called_once()
