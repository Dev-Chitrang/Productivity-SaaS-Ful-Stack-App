import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.core.email import SMTPEmailProvider, BrevoEmailProvider


class TestSMTPEmailProvider:
    @pytest.fixture
    def provider(self):
        return SMTPEmailProvider()

    @patch("app.core.email.smtplib.SMTP")
    def test_send_plain_text(self, mock_smtp, provider):
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        with patch("app.core.email.settings") as mock_settings:
            mock_settings.SMTP_FROM_EMAIL = "noreply@example.com"
            mock_settings.SMTP_HOST = "localhost"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USE_TLS = False
            mock_settings.SMTP_USER = None
            mock_settings.SMTP_PASSWORD = None
            provider.send("test@example.com", "Subject", "Body content")

        mock_server.sendmail.assert_called_once()

    @patch("app.core.email.smtplib.SMTP")
    def test_send_with_tls_and_auth(self, mock_smtp, provider):
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        with patch("app.core.email.settings") as mock_settings:
            mock_settings.SMTP_FROM_EMAIL = "noreply@example.com"
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USE_TLS = True
            mock_settings.SMTP_USER = "user"
            mock_settings.SMTP_PASSWORD = "pass"
            provider.send("test@example.com", "Subject", "Body content")

        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user", "pass")
        mock_server.sendmail.assert_called_once()

    @patch("app.core.email.smtplib.SMTP")
    def test_send_html_no_attachments(self, mock_smtp, provider):
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        with patch("app.core.email.settings") as mock_settings:
            mock_settings.SMTP_FROM_EMAIL = "noreply@example.com"
            mock_settings.SMTP_HOST = "localhost"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USE_TLS = False
            mock_settings.SMTP_USER = None
            mock_settings.SMTP_PASSWORD = None

            provider.send_html(
                "test@example.com",
                "HTML Subject",
                "<h1>Hello</h1>",
                text_body="Hello",
            )

        mock_server.sendmail.assert_called_once()

    @patch("app.core.email.smtplib.SMTP")
    def test_send_html_with_attachments(self, mock_smtp, provider):
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        with patch("app.core.email.settings") as mock_settings:
            mock_settings.SMTP_FROM_EMAIL = "noreply@example.com"
            mock_settings.SMTP_HOST = "localhost"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USE_TLS = False
            mock_settings.SMTP_USER = None
            mock_settings.SMTP_PASSWORD = None

            attachments = [
                {"filename": "report.pdf", "content": b"pdf_content", "content_type": "application/pdf"},
                {"filename": "data.csv", "content": b"csv_content", "content_type": "text/csv"},
            ]

            provider.send_html(
                "test@example.com",
                "Report",
                "<h1>Report</h1>",
                text_body="Report",
                attachments=attachments,
            )

        mock_server.sendmail.assert_called_once()

    @patch("app.core.email.smtplib.SMTP")
    def test_send_html_without_text_body(self, mock_smtp, provider):
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        with patch("app.core.email.settings") as mock_settings:
            mock_settings.SMTP_FROM_EMAIL = "noreply@example.com"
            mock_settings.SMTP_HOST = "localhost"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USE_TLS = False
            mock_settings.SMTP_USER = None
            mock_settings.SMTP_PASSWORD = None

            provider.send_html(
                "test@example.com",
                "HTML Only",
                "<h1>Hello</h1>",
            )

        mock_server.sendmail.assert_called_once()


class TestBrevoEmailProvider:
    @patch("brevo.AsyncBrevo")
    def test_send_plain_text(self, mock_brevo_cls):
        mock_client = AsyncMock()
        mock_brevo_cls.return_value = mock_client

        with patch("app.core.email.settings") as mock_settings:
            mock_settings.BREVO_API_KEY = "test_key"
            mock_settings.BREVO_FROM_EMAIL = "noreply@example.com"
            provider = BrevoEmailProvider()
            provider.send("test@example.com", "Subject", "Body content")

        mock_client.transactional_emails.send_transac_email.assert_called_once()

    @patch("brevo.AsyncBrevo")
    def test_send_html(self, mock_brevo_cls):
        mock_client = AsyncMock()
        mock_brevo_cls.return_value = mock_client

        with patch("app.core.email.settings") as mock_settings:
            mock_settings.BREVO_API_KEY = "test_key"
            mock_settings.BREVO_FROM_EMAIL = "noreply@example.com"
            provider = BrevoEmailProvider()

            provider.send_html(
                "test@example.com",
                "HTML Subject",
                "<h1>Hello</h1>",
                text_body="Hello",
            )

        mock_client.transactional_emails.send_transac_email.assert_called_once()

    @patch("brevo.AsyncBrevo")
    def test_send_html_with_attachments(self, mock_brevo_cls):
        mock_client = AsyncMock()
        mock_brevo_cls.return_value = mock_client

        with patch("app.core.email.settings") as mock_settings:
            mock_settings.BREVO_API_KEY = "test_key"
            mock_settings.BREVO_FROM_EMAIL = "noreply@example.com"
            provider = BrevoEmailProvider()

            attachments = [
                {"filename": "report.pdf", "content": b"pdf_content"},
            ]
            provider.send_html(
                "test@example.com",
                "Report",
                "<h1>Report</h1>",
                text_body="Report",
                attachments=attachments,
            )

        mock_client.transactional_emails.send_transac_email.assert_called_once()

    @patch("brevo.AsyncBrevo")
    def test_send_html_without_text_body(self, mock_brevo_cls):
        mock_client = AsyncMock()
        mock_brevo_cls.return_value = mock_client

        with patch("app.core.email.settings") as mock_settings:
            mock_settings.BREVO_API_KEY = "test_key"
            mock_settings.BREVO_FROM_EMAIL = "noreply@example.com"
            provider = BrevoEmailProvider()

            provider.send_html(
                "test@example.com",
                "HTML Only",
                "<h1>Hello</h1>",
            )

        mock_client.transactional_emails.send_transac_email.assert_called_once()
