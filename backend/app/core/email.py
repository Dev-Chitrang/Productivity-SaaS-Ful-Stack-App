import abc
import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from app.core.config import settings


class EmailProvider(abc.ABC):
    @abc.abstractmethod
    def send(self, recipient: str, subject: str, body: str) -> None:
        ...

    @abc.abstractmethod
    def send_html(
        self,
        recipient: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
        attachments: list | None = None,
    ) -> None:
        ...


class SMTPEmailProvider(EmailProvider):
    def send(self, recipient: str, subject: str, body: str) -> None:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = recipient

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(msg["From"], [recipient], msg.as_string())

    def send_html(
        self,
        recipient: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
        attachments: list | None = None,
    ) -> None:
        body = MIMEMultipart("alternative")
        body.attach(MIMEText(text_body or html_body, "plain"))
        body.attach(MIMEText(html_body, "html"))

        if attachments:
            msg = MIMEMultipart("mixed")
            msg.attach(body)
            for att in attachments:
                content_type = att.get("content_type", "application/octet-stream")
                subtype = content_type.split("/")[-1] if "/" in content_type else "octet-stream"
                part = MIMEApplication(att["content"], _subtype=subtype)
                part.add_header("Content-Disposition", "attachment", filename=att["filename"])
                msg.attach(part)
        else:
            msg = body

        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = recipient

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(msg["From"], [recipient], msg.as_string())


class BrevoEmailProvider(EmailProvider):
    def __init__(self):
        from brevo import AsyncBrevo
        self._client = AsyncBrevo(api_key=settings.BREVO_API_KEY)
        self._from_email = settings.BREVO_FROM_EMAIL

    def send(self, recipient: str, subject: str, body: str) -> None:
        async def _send():
            await self._client.transactional_emails.send_transac_email(
                sender={"email": self._from_email, "name": "My App"},
                to=[{"email": recipient}],
                subject=subject,
                text_content=body,
            )
        asyncio.run(_send())

    def send_html(
        self,
        recipient: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
        attachments: list | None = None,
    ) -> None:
        async def _send():
            params = {
                "sender": {"email": self._from_email, "name": "My App"},
                "to": [{"email": recipient}],
                "subject": subject,
                "html_content": html_body,
            }
            if text_body:
                params["text_content"] = text_body
            if attachments:
                brevo_attachments = []
                for att in attachments:
                    brevo_attachments.append({
                        "name": att["filename"],
                        "content": att["content"],
                    })
                params["attachment"] = brevo_attachments
            await self._client.transactional_emails.send_transac_email(**params)
        asyncio.run(_send())
