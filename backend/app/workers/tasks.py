import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from celery import Celery
from app.core.config import settings

celery_app = Celery("productivity_tasks", broker=settings.REDIS_CELERY_BROKER_URL)

celery_app.conf.beat_schedule = {
    "run-omni-reminder-engine-sweeps": {
        "task": "tasks.process_all_reminders",
        "schedule": 1800.0,  # Executes every 30 minutes (1800 seconds)
    },
}

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
    name="tasks.send_html_email",
    autoretry_for=(smtplib.SMTPException,),
    retry_backoff=True,
    max_retries=3
)
def send_html_email(recipient: str, subject: str, html_body: str, text_body: str | None = None):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = recipient

    msg.attach(MIMEText(text_body or html_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(msg["From"], [recipient], msg.as_string())


@celery_app.task(name="tasks.process_all_reminders")
def process_all_reminders():
    """Main periodic gateway loop triggered by Celery Beat."""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_run_all_reminder_scans())


async def _run_all_reminder_scans():
    now = datetime.now(timezone.utc)
    today = now.date()

    async with async_session_factory() as session:
        repo = ReminderRepository(session)

        # 1. ORCHESTRATE MEETING REMINDERS
        meetings = await repo.fetch_scheduled_meetings_for_reminders(now)
        for meeting in meetings:
            # Check host's configurations matching rules
            settings_stmt = "SELECT meetings_config, schedule_all, reminders_enabled FROM user_reminder_settings WHERE user_id = :uid"
            user_setting = (await session.execute(text(settings_stmt), {"uid": meeting.scheduled_by})).fetchone()

            if user_setting and user_setting.reminders_enabled and (user_setting.schedule_all or user_setting.meetings_config.get("enabled", True)):
                invite_stmt = "SELECT name, email FROM meeting_invitations WHERE meeting_id = :mid"
                invites = (await session.execute(text(invite_stmt), {"mid": meeting.id})).all()

                for invite in invites:
                    subject = f"Reminder: Meeting '{meeting.title}'"
                    body = (
                        f"Hi {invite.name},\n\n"
                        f"This is a reminder for your upcoming scheduled meeting:\n"
                        f"Title: {meeting.title}\n"
                        f"Time: {meeting.scheduled_start.strftime('%Y-%m-%d %H:%M')} ({meeting.timezone})\n"
                        f"Agenda: {meeting.agenda or 'N/A'}\n\n"
                        f"Join link: {settings.FRONTEND_URL}/meetings/{meeting.id}"
                    )
                    send_async_email.delay(invite.email, subject, body)

        # 2. ORCHESTRATE CALENDAR REMINDERS
        events = await repo.fetch_calendar_events_for_reminders(now)
        for event in events:
            settings_stmt = "SELECT calendar_config, schedule_all, reminders_enabled FROM user_reminder_settings WHERE user_id = :uid"
            user_setting = (await session.execute(text(settings_stmt), {"uid": event.user_id})).fetchone()

            if user_setting and user_setting.reminders_enabled and (user_setting.schedule_all or user_setting.calendar_config.get("enabled", True)):
                user_stmt = "SELECT email, username FROM users WHERE id = :uid"
                user = (await session.execute(text(user_stmt), {"uid": event.user_id})).fetchone()
                if user:
                    subject = f"Calendar Reminder: {event.title}"
                    body = (
                        f"Hello {user.username},\n\n"
                        f"You have an upcoming calendar event:\n"
                        f"Event: {event.title}\n"
                        f"Starts At: {event.start_time.strftime('%Y-%m-%d %H:%M')}\n"
                        f"Description: {event.description or 'No description provided.'}"
                    )
                    send_async_email.delay(user.email, subject, body)

        # 3. ORCHESTRATE TASK REMINDERS
        tasks = await repo.fetch_tasks_for_reminders(today)
        for task in tasks:
            settings_stmt = "SELECT tasks_config, schedule_all, reminders_enabled FROM user_reminder_settings WHERE user_id = :uid"
            user_setting = (await session.execute(text(settings_stmt), {"uid": task.user_id})).fetchone()

            if user_setting and user_setting.reminders_enabled and (user_setting.schedule_all or user_setting.tasks_config.get("enabled", True)):
                user_stmt = "SELECT email, username FROM users WHERE id = :uid"
                user = (await session.execute(text(user_stmt), {"uid": task.user_id})).fetchone()
                if user:
                    status_lbl = "OVERDUE" if task.due_date < today else "DUE TODAY/UPCOMING"
                    subject = f"Task Alert [{status_lbl}]: {task.title}"
                    body = (
                        f"Hello {user.username},\n\n"
                        f"This is a status notification for an outstanding task assignment:\n"
                        f"Task: {task.title}\n"
                        f"Due Date: {task.due_date.strftime('%Y-%m-%d')}\n"
                        f"Status: {status_lbl}"
                    )
                    send_async_email.delay(user.email, subject, body)
