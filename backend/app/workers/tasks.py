from celery import Celery
from app.core.config import settings
from app.core.providers import get_email_provider

celery_app = Celery("productivity_tasks", broker=settings.REDIS_CELERY_BROKER_URL)

celery_app.conf.beat_schedule = {
    "run-omni-reminder-engine-sweeps": {
        "task": "tasks.process_all_reminders",
        "schedule": 1800.0,  # Executes every 30 minutes (1800 seconds)
    },
}

def _email_provider():
    return get_email_provider()

@celery_app.task(
    name="tasks.send_async_email",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3
)
def send_async_email(recipient: str, subject: str, body: str):
    _email_provider().send(recipient, subject, body)


@celery_app.task(
    name="tasks.send_html_email",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3
)
def send_html_email(recipient: str, subject: str, html_body: str, text_body: str | None = None, attachments: list | None = None):
    _email_provider().send_html(recipient, subject, html_body, text_body, attachments)


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

@celery_app.task(
    name="tasks.analyze_meeting_transcript",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3
)
def analyze_meeting_transcript(session_id_str: str):
    """Orchestrates AI analysis and completion email for a meeting session.

    Only receives session_id; all other data is loaded from the database.
    """
    import asyncio
    from uuid import UUID
    from app.core.database import async_session_factory
    from app.core.logger import logger
    from app.core.providers import get_storage_service
    from app.modules.meetings.repository import MeetingRepository, MeetingAIAnalysisRepository, MeetingSessionRepository
    from app.modules.meetings.ai_provider_service import AIProviderService
    from app.modules.meetings.service import MeetingAIAnalysisService
    from app.modules.meetings.completion_service import MeetingCompletionService
    from app.modules.meetings.enums import AIAnalysisStatus

    session_id = UUID(session_id_str)

    async def _run():
        async with async_session_factory() as session:
            meeting_repo = MeetingRepository(session)
            session_repo = MeetingSessionRepository(session)
            ai_repo = MeetingAIAnalysisRepository(session)
            storage_svc = get_storage_service("meetings")

            meeting_session = await session_repo.get_by_id(session_id)
            if not meeting_session:
                logger.error(f"Session {session_id} not found for completion pipeline")
                return

            meeting = await meeting_repo.get_by_id(meeting_session.meeting_id)
            if not meeting:
                logger.error(f"Meeting {meeting_session.meeting_id} not found for completion pipeline")
                return

            logger.info(f"Session {session_id} (meeting {meeting.id}) found for completion pipeline")

            transcripts = await meeting_repo.list_transcripts_by_session(session_id)
            logger.info(f"Transcript lookup for session {session_id}: {len(transcripts)} transcript(s) found")

            analysis_attempted = False

            if not transcripts:
                logger.warning(f"No transcripts found for session {session_id}, will retry")
                raise Exception(f"Transcript not yet available for session {session_id}")

            transcript_text = ""
            tx_path = transcripts[0].storage_path
            try:
                raw = await storage_svc.read(tx_path)
                transcript_text = raw.decode("utf-8")
                logger.info(f"Transcript file loaded: {tx_path} ({len(transcript_text)} chars)")
            except Exception as e:
                logger.error(f"Failed to read transcript file {tx_path}: {e}")
                raise

            if not transcript_text:
                logger.error(f"Transcript file {tx_path} is empty for session {session_id}, marking analysis as FAILED")
                analysis_placeholder = await ai_repo.get_by_session_id(session_id)
                if not analysis_placeholder:
                    analysis_placeholder = await ai_repo.create_analysis_placeholder(session_id)
                await ai_repo.update_status(
                    analysis_placeholder.id,
                    AIAnalysisStatus.FAILED,
                    raw_response={"error": "Transcript file is empty"},
                )
            else:
                from app.modules.meetings.transcript_preprocessor import preprocess_transcript
                cleaned_transcript = preprocess_transcript(transcript_text)

                logger.info(f"Starting AI analysis request for session {session_id}")

                provider = AIProviderService()
                ai_service = MeetingAIAnalysisService(ai_repo, provider)
                await ai_service.process_async_transcript_analysis(
                    session_id=session_id,
                    agenda=meeting.agenda or "",
                    transcript_text=cleaned_transcript,
                )

                analysis_attempted = True
                logger.info(f"AI analysis completed for session {session_id}")

            logger.info(f"Starting completion email dispatch for session {session_id}")
            completion_service = MeetingCompletionService(session, storage=storage_svc)
            await completion_service.send_completion_email(session_id)
            logger.info(f"Completion email dispatch completed for session {session_id}")

            await session.commit()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(_run())
