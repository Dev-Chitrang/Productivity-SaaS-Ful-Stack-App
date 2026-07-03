import smtplib
from email.mime.text import MIMEText
from celery import Celery
from app.core.config import settings

celery_app = Celery("productivity_tasks", broker=settings.REDIS_CELERY_BROKER_URL)

@celery_app.task(
    name="tasks.send_async_email",
    autoretry_for=(smtplib.SMTPException,),
    retry_backoff=True,
    max_retries=3
)
def send_async_email(recipient: str, subject: str, body: str):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = recipient

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        # 1. Handle TLS securely if required
        if settings.SMTP_USE_TLS:
            server.starttls()

        # 2. Always attempt to authenticate outside the TLS condition if credentials exist
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

        server.sendmail(msg["From"], [recipient], msg.as_string())


@celery_app.task(
    name="tasks.send_meeting_invitation",
    autoretry_for=(smtplib.SMTPException,),
    retry_backoff=True,
    max_retries=3
)
def send_meeting_invitation(recipient: str, subject: str, body: str):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = recipient

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        # 1. Handle TLS securely if required
        if settings.SMTP_USE_TLS:
            server.starttls()

        # 2. Always attempt to authenticate outside the TLS condition if credentials exist
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

        server.sendmail(msg["From"], [recipient], msg.as_string())
