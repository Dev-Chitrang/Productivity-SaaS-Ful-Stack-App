import pytest
import uuid
import asyncio
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy import text as real_text
from app.workers.tasks import send_async_email, send_html_email, analyze_meeting_transcript, process_all_reminders, celery_app
from app.core.providers import get_email_provider
from app.modules.meetings.enums import AIAnalysisStatus


class TestSendAsyncEmailTask:
    def test_task_name(self):
        assert send_async_email.name == "tasks.send_async_email"

    def test_autoretry_for_exception(self):
        assert send_async_email.autoretry_for == (Exception,)

    def test_max_retries(self):
        assert send_async_email.max_retries == 3

    @patch("app.workers.tasks.get_email_provider")
    def test_send_calls_provider(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.send = MagicMock()
        mock_get_provider.return_value = mock_provider

        send_async_email("test@example.com", "Subject", "Body")

        mock_provider.send.assert_called_once_with("test@example.com", "Subject", "Body")
        mock_get_provider.assert_called_once()

    @patch("app.workers.tasks.get_email_provider")
    def test_send_propagates_exception(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.send = MagicMock(side_effect=Exception("SMTP error"))
        mock_get_provider.return_value = mock_provider

        with pytest.raises(Exception, match="SMTP error"):
            send_async_email("test@example.com", "Subject", "Body")

    @patch("app.workers.tasks.get_email_provider")
    def test_send_with_retry_logic(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.send = MagicMock(side_effect=[Exception("fail"), None])
        mock_get_provider.return_value = mock_provider

        with pytest.raises(Exception):
            send_async_email("test@example.com", "Subject", "Body")

        assert mock_provider.send.call_count == 1


class TestSendHtmlEmailTask:
    def test_task_name(self):
        assert send_html_email.name == "tasks.send_html_email"

    def test_autoretry_for_exception(self):
        assert send_html_email.autoretry_for == (Exception,)

    def test_max_retries(self):
        assert send_html_email.max_retries == 3

    @patch("app.workers.tasks.get_email_provider")
    def test_send_html_calls_provider(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.send_html = MagicMock()
        mock_get_provider.return_value = mock_provider

        send_html_email(
            recipient="test@example.com",
            subject="HTML Subject",
            html_body="<h1>Hello</h1>",
            text_body="Hello",
        )

        mock_provider.send_html.assert_called_once_with(
            "test@example.com", "HTML Subject", "<h1>Hello</h1>", "Hello", None
        )

    @patch("app.workers.tasks.get_email_provider")
    def test_send_html_with_attachments(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.send_html = MagicMock()
        mock_get_provider.return_value = mock_provider

        attachments = [
            {"filename": "report.pdf", "content": b"pdf_content", "content_type": "application/pdf"}
        ]
        send_html_email(
            recipient="test@example.com",
            subject="Report",
            html_body="<h1>Report</h1>",
            text_body="Report",
            attachments=attachments,
        )

        mock_provider.send_html.assert_called_once_with(
            "test@example.com", "Report", "<h1>Report</h1>", "Report", attachments
        )

    @patch("app.workers.tasks.get_email_provider")
    def test_send_html_without_text_body(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.send_html = MagicMock()
        mock_get_provider.return_value = mock_provider

        send_html_email(
            recipient="test@example.com",
            subject="HTML Subject",
            html_body="<h1>Hello</h1>",
        )

        mock_provider.send_html.assert_called_once_with(
            "test@example.com", "HTML Subject", "<h1>Hello</h1>", None, None
        )


class TestAnalyzeMeetingTranscript:
    @patch("asyncio.get_event_loop")
    @patch("app.modules.meetings.completion_service.MeetingCompletionService")
    @patch("app.modules.meetings.service.MeetingAIAnalysisService")
    @patch("app.modules.meetings.ai_provider_service.AIProviderService")
    @patch("app.modules.meetings.repository.MeetingAIAnalysisRepository")
    @patch("app.modules.meetings.repository.MeetingSessionRepository")
    @patch("app.modules.meetings.repository.MeetingRepository")
    @patch("app.core.database.async_session_factory", create=True)
    @patch("app.core.providers.get_storage_service")
    @patch("app.modules.meetings.transcript_preprocessor.preprocess_transcript")
    def test_analyze_transcript_success_flow(
        self, mock_preprocess, mock_get_storage, mock_session_factory,
        mock_meeting_repo_cls, mock_session_repo_cls, mock_ai_repo_cls,
        mock_ai_provider_cls, mock_ai_service_cls, mock_completion_service_cls, mock_get_event_loop
    ):
        mock_loop = MagicMock()
        mock_loop.run_until_complete = MagicMock(side_effect=lambda coro: asyncio.run(coro))
        mock_get_event_loop.return_value = mock_loop

        mock_session = AsyncMock()
        mock_session_factory.return_value = AsyncMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_meeting = AsyncMock()
        mock_meeting.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_meeting.agenda = "Agenda"
        mock_session_repo_cls.return_value = AsyncMock()
        mock_meeting_repo_cls.return_value = AsyncMock()
        mock_meeting_repo_cls.return_value.get_by_id.return_value = mock_meeting

        mock_transcript = MagicMock()
        mock_transcript.storage_path = "/tmp/tx.txt"
        mock_meeting_repo_cls.return_value.list_transcripts_by_session.return_value = [mock_transcript]

        mock_storage = AsyncMock()
        mock_storage.read.return_value = b"raw transcript"
        mock_get_storage.return_value = mock_storage

        mock_preprocess.return_value = "cleaned transcript"

        mock_provider = AsyncMock()
        mock_ai_provider_cls.return_value = mock_provider
        mock_ai_repo = AsyncMock()
        mock_ai_repo_cls.return_value = mock_ai_repo

        mock_analysis = MagicMock()
        mock_analysis.id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        mock_ai_repo.get_by_session_id.return_value = None
        mock_ai_repo.create_analysis_placeholder.return_value = mock_analysis

        mock_ai_service = AsyncMock()
        mock_ai_service_cls.return_value = mock_ai_service

        mock_completion_service = AsyncMock()
        mock_completion_service_cls.return_value = mock_completion_service

        session_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        analyze_meeting_transcript(str(session_id))

        mock_ai_service.process_async_transcript_analysis.assert_called_once()
        mock_completion_service.send_completion_email.assert_called_once_with(session_id)

    @patch("asyncio.get_event_loop")
    @patch("app.modules.meetings.completion_service.MeetingCompletionService")
    @patch("app.core.database.async_session_factory", create=True)
    @patch("app.core.providers.get_storage_service")
    def test_analyze_transcript_no_meeting_session_logs_error(
        self, mock_get_storage, mock_session_factory, mock_completion_service_cls, mock_get_event_loop
    ):
        mock_loop = MagicMock()
        mock_loop.run_until_complete = MagicMock(side_effect=lambda coro: asyncio.run(coro))
        mock_get_event_loop.return_value = mock_loop

        mock_session_factory.return_value = AsyncMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock()
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        from app.modules.meetings.repository import MeetingSessionRepository
        mock_session_repo = MagicMock()
        mock_session_repo.get_by_id = AsyncMock(return_value=None)
        with patch("app.modules.meetings.repository.MeetingSessionRepository", return_value=mock_session_repo):
            session_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
            analyze_meeting_transcript(str(session_id))

        mock_session_repo.get_by_id.assert_called_once_with(session_id)

    @patch("asyncio.get_event_loop")
    @patch("app.modules.meetings.completion_service.MeetingCompletionService")
    @patch("app.modules.meetings.service.MeetingAIAnalysisService")
    @patch("app.modules.meetings.ai_provider_service.AIProviderService")
    @patch("app.modules.meetings.repository.MeetingAIAnalysisRepository")
    @patch("app.modules.meetings.repository.MeetingSessionRepository")
    @patch("app.modules.meetings.repository.MeetingRepository")
    @patch("app.core.database.async_session_factory", create=True)
    @patch("app.core.providers.get_storage_service")
    def test_analyze_transcript_empty_file_logs_error(
        self, mock_get_storage, mock_session_factory, mock_meeting_repo_cls,
        mock_session_repo_cls, mock_ai_repo_cls, mock_ai_provider_cls,
        mock_ai_service_cls, mock_completion_service_cls, mock_get_event_loop
    ):
        mock_loop = MagicMock()
        mock_loop.run_until_complete = MagicMock(side_effect=lambda coro: asyncio.run(coro))
        mock_get_event_loop.return_value = mock_loop

        mock_session = AsyncMock()
        mock_session_factory.return_value = AsyncMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_session.meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_session_repo_cls.return_value = AsyncMock()
        mock_meeting_repo_cls.return_value = AsyncMock()
        mock_meeting_repo_cls.return_value.get_by_id.return_value = mock_session
        mock_transcript = MagicMock()
        mock_transcript.storage_path = "/tmp/tx.txt"
        mock_meeting_repo_cls.return_value.list_transcripts_by_session.return_value = [mock_transcript]
        mock_get_storage.return_value = AsyncMock()
        mock_get_storage.return_value.read.return_value = b""

        mock_ai_repo = AsyncMock()
        mock_ai_repo_cls.return_value = mock_ai_repo
        mock_placeholder = MagicMock()
        mock_placeholder.id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        mock_ai_repo.get_by_session_id.return_value = None
        mock_ai_repo.create_analysis_placeholder.return_value = mock_placeholder

        mock_completion_service = AsyncMock()
        mock_completion_service_cls.return_value = mock_completion_service

        session_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        analyze_meeting_transcript(str(session_id))

        mock_ai_repo.update_status.assert_called_with(
            mock_placeholder.id,
            AIAnalysisStatus.FAILED,
            raw_response={"error": "Transcript file is empty"},
        )

    @patch("asyncio.get_event_loop")
    @patch("app.modules.meetings.completion_service.MeetingCompletionService")
    @patch("app.modules.meetings.service.MeetingAIAnalysisService")
    @patch("app.modules.meetings.ai_provider_service.AIProviderService")
    @patch("app.modules.meetings.repository.MeetingAIAnalysisRepository")
    @patch("app.modules.meetings.repository.MeetingSessionRepository")
    @patch("app.modules.meetings.repository.MeetingRepository")
    @patch("app.core.database.async_session_factory", create=True)
    @patch("app.core.providers.get_storage_service")
    def test_analyze_transcript_provider_error_propagates(
        self, mock_get_storage, mock_session_factory, mock_meeting_repo_cls,
        mock_session_repo_cls, mock_ai_repo_cls, mock_ai_provider_cls,
        mock_ai_service_cls, mock_completion_service_cls, mock_get_event_loop
    ):
        mock_loop = MagicMock()
        mock_loop.run_until_complete = MagicMock(side_effect=lambda coro: asyncio.run(coro))
        mock_get_event_loop.return_value = mock_loop

        mock_session = AsyncMock()
        mock_session.meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_session_repo_cls.return_value = AsyncMock()
        mock_meeting_repo_cls.return_value = AsyncMock()
        mock_meeting_repo_cls.return_value.get_by_id.return_value = mock_session
        mock_meeting_repo_cls.return_value.list_transcripts_by_session.return_value = [
            MagicMock(storage_path="/tmp/tx.txt")
        ]
        mock_storage = AsyncMock()
        mock_storage.read.return_value = b"raw transcript"
        mock_get_storage.return_value = mock_storage
        mock_ai_provider_cls.return_value = AsyncMock()

        with patch("app.modules.meetings.transcript_preprocessor.preprocess_transcript", return_value="cleaned"):
            mock_ai_service = AsyncMock()
            mock_ai_service.process_async_transcript_analysis.side_effect = Exception("AI error")
            mock_ai_service_cls.return_value = mock_ai_service
            mock_ai_repo = AsyncMock()
            mock_ai_repo_cls.return_value = mock_ai_repo
            mock_analysis = MagicMock()
            mock_analysis.id = uuid.UUID("87654321-4321-8765-4321-876543218765")
            mock_ai_repo.get_by_session_id.return_value = None
            mock_ai_repo.create_analysis_placeholder.return_value = mock_analysis

            session_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
            with pytest.raises(Exception, match="AI error"):
                analyze_meeting_transcript(str(session_id))


class TestProcessAllReminders:
    def test_celery_beat_config(self):
        assert "run-omni-reminder-engine-sweeps" in celery_app.conf.beat_schedule
        entry = celery_app.conf.beat_schedule["run-omni-reminder-engine-sweeps"]
        assert entry["task"] == "tasks.process_all_reminders"
        assert entry["schedule"] == 1800.0

    def test_task_name(self):
        assert process_all_reminders.name == "tasks.process_all_reminders"

    @patch("app.workers.tasks._run_all_reminder_scans", new_callable=AsyncMock)
    @patch("app.workers.tasks.asyncio")
    def test_process_all_reminders_runs_scan(self, mock_asyncio, mock_scan):
        process_all_reminders()
        mock_asyncio.run.assert_called_once()

    @patch("app.workers.tasks.send_async_email")
    @patch("app.workers.tasks.async_session_factory", create=True)
    @patch("app.workers.tasks.timezone", create=True)
    @patch("app.workers.tasks.datetime", create=True)
    async def test_run_all_reminder_scans_no_data(self, mock_datetime, mock_timezone, mock_session_factory, mock_send_email):
        from app.workers.tasks import _run_all_reminder_scans

        now = datetime.now(timezone.utc)
        mock_datetime.now.return_value = now
        mock_timezone.utc = timezone.utc

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session_factory.return_value = mock_session

        mock_execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_result.fetchone.return_value = None
        mock_execute.return_value = mock_result
        mock_session.execute = mock_execute

        with patch("app.workers.tasks.ReminderRepository", create=True) as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.fetch_scheduled_meetings_for_reminders.return_value = []
            mock_repo.fetch_calendar_events_for_reminders.return_value = []
            mock_repo.fetch_tasks_for_reminders.return_value = []
            mock_repo_cls.return_value = mock_repo
            await _run_all_reminder_scans()

        mock_send_email.delay.assert_not_called()

    @patch("app.workers.tasks.send_async_email")
    @patch("app.workers.tasks.text", create=True)
    @patch("app.workers.tasks.AsyncSessionLocal", create=True)
    @patch("app.workers.tasks.timezone", create=True)
    @patch("app.workers.tasks.datetime", create=True)
    async def test_run_all_reminder_scans_with_meeting(self, mock_datetime, mock_timezone, mock_session_factory, mock_text, mock_send_email):
        from app.workers.tasks import _run_all_reminder_scans

        now = datetime.now(timezone.utc)
        mock_datetime.now.return_value = now
        mock_timezone.utc = timezone.utc
        mock_text.side_effect = lambda sql: real_text(sql)

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session_factory.return_value = mock_session

        mock_meeting = MagicMock()
        mock_meeting.id = uuid.uuid4()
        mock_meeting.scheduled_by = uuid.uuid4()
        mock_meeting.title = "Test Meeting"
        mock_meeting.scheduled_start = now
        mock_meeting.timezone = "UTC"
        mock_meeting.agenda = "Discuss"

        mock_execute = AsyncMock()
        mock_session.execute = mock_execute

        def execute_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            if "meeting_invitations" in str(args[0]):
                mock_result.all.return_value = [
                    MagicMock(name="Invitee", email="invitee@example.com")
                ]
            elif "user_reminder_settings" in str(args[0]):
                mock_result.fetchone.return_value = MagicMock(
                    reminders_enabled=True, schedule_all=True,
                    meetings_config={"enabled": True}
                )
            elif "users" in str(args[0]):
                mock_result.fetchone.return_value = None
            else:
                mock_result.all.return_value = []
                mock_result.fetchone.return_value = None
            return mock_result

        mock_execute.side_effect = execute_side_effect

        with patch("app.workers.tasks.ReminderRepository", create=True) as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.fetch_scheduled_meetings_for_reminders.return_value = [mock_meeting]
            mock_repo.fetch_calendar_events_for_reminders.return_value = []
            mock_repo.fetch_tasks_for_reminders.return_value = []
            mock_repo_cls.return_value = mock_repo
            await _run_all_reminder_scans()

        mock_send_email.delay.assert_called_once()

    @patch("app.workers.tasks.send_async_email")
    @patch("app.workers.tasks.text", create=True)
    @patch("app.workers.tasks.AsyncSessionLocal", create=True)
    @patch("app.workers.tasks.timezone", create=True)
    @patch("app.workers.tasks.datetime", create=True)
    async def test_run_all_reminder_scans_disabled_settings(self, mock_datetime, mock_timezone, mock_session_factory, mock_text, mock_send_email):
        from app.workers.tasks import _run_all_reminder_scans

        now = datetime.now(timezone.utc)
        mock_datetime.now.return_value = now
        mock_timezone.utc = timezone.utc
        mock_text.side_effect = lambda sql: real_text(sql)

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session_factory.return_value = mock_session

        mock_meeting = MagicMock()
        mock_meeting.scheduled_by = uuid.uuid4()

        mock_execute = AsyncMock()
        mock_session.execute = mock_execute

        def execute_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            if "user_reminder_settings" in str(args[0]):
                mock_result.fetchone.return_value = MagicMock(
                    reminders_enabled=False, schedule_all=False
                )
            else:
                mock_result.all.return_value = []
                mock_result.fetchone.return_value = None
            return mock_result

        mock_execute.side_effect = execute_side_effect

        with patch("app.workers.tasks.ReminderRepository", create=True) as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.fetch_scheduled_meetings_for_reminders.return_value = [mock_meeting]
            mock_repo.fetch_calendar_events_for_reminders.return_value = []
            mock_repo.fetch_tasks_for_reminders.return_value = []
            mock_repo_cls.return_value = mock_repo
            await _run_all_reminder_scans()

        mock_send_email.delay.assert_not_called()



# ── Task metadata ─────────────────────────────────────────────────────────────

class TestTaskMetadata:
    def test_send_async_email_retry_backoff(self):
        assert send_async_email.retry_backoff is True

    def test_send_html_email_retry_backoff(self):
        assert send_html_email.retry_backoff is True

    def test_analyze_transcript_max_retries(self):
        assert analyze_meeting_transcript.max_retries == 3

    def test_analyze_transcript_autoretry(self):
        assert analyze_meeting_transcript.autoretry_for == (Exception,)

    def test_analyze_transcript_retry_backoff(self):
        assert analyze_meeting_transcript.retry_backoff is True

    def test_celery_app_name(self):
        assert celery_app.main == "productivity_tasks"

    def test_send_async_email_has_delay(self):
        """Celery tasks must expose .delay() for async dispatch."""
        assert callable(send_async_email.delay)

    def test_send_html_email_has_delay(self):
        assert callable(send_html_email.delay)

    def test_analyze_transcript_has_delay(self):
        assert callable(analyze_meeting_transcript.delay)


# ── send_async_email — additional scenarios ───────────────────────────────────

class TestSendAsyncEmailAdditional:
    @patch("app.workers.tasks.get_email_provider")
    def test_send_called_with_all_positional_args(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider
        send_async_email("to@example.com", "Subject Line", "Body text")
        mock_provider.send.assert_called_once_with("to@example.com", "Subject Line", "Body text")

    @patch("app.workers.tasks.get_email_provider")
    def test_email_provider_created_each_call(self, mock_get_provider):
        """Provider factory should be called once per task execution."""
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider
        send_async_email("a@example.com", "S", "B")
        assert mock_get_provider.call_count == 1

    @patch("app.workers.tasks.get_email_provider")
    def test_provider_exception_propagates_for_retry(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.send.side_effect = ConnectionError("no route to host")
        mock_get_provider.return_value = mock_provider
        with pytest.raises(ConnectionError):
            send_async_email("a@example.com", "S", "B")


# ── send_html_email — additional scenarios ────────────────────────────────────

class TestSendHtmlEmailAdditional:
    @patch("app.workers.tasks.get_email_provider")
    def test_none_attachments_passed_as_none(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider
        send_html_email("a@example.com", "S", "<b>hi</b>")
        call_args = mock_provider.send_html.call_args[0]
        assert call_args[4] is None  # attachments

    @patch("app.workers.tasks.get_email_provider")
    def test_html_email_exception_propagates(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.send_html.side_effect = Exception("Brevo down")
        mock_get_provider.return_value = mock_provider
        with pytest.raises(Exception, match="Brevo down"):
            send_html_email("a@example.com", "S", "<b>hi</b>")


# ── analyze_meeting_transcript — additional scenarios ─────────────────────────

def _build_analyze_patches(
    meeting_session=None,
    meeting=None,
    transcripts=None,
    transcript_content=b"transcript text",
    ai_service_raises=None,
    storage_raises=None,
    analysis_placeholder=None,
    existing_analysis=None,
):
    """Factory for the patch stack used by analyze_meeting_transcript tests."""
    mock_meeting_session = meeting_session or MagicMock(
        meeting_id=uuid.UUID("12345678-1234-5678-1234-567812345678")
    )
    mock_meeting = meeting or MagicMock(
        id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        agenda="Agenda text",
    )
    mock_transcripts = transcripts
    mock_storage = AsyncMock()
    if storage_raises:
        mock_storage.read = AsyncMock(side_effect=storage_raises)
    else:
        mock_storage.read = AsyncMock(return_value=transcript_content)

    mock_placeholder = analysis_placeholder or MagicMock(
        id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    )

    return (
        mock_meeting_session, mock_meeting, mock_transcripts,
        mock_storage, mock_placeholder, existing_analysis, ai_service_raises
    )


class TestAnalyzeMeetingTranscriptAdditional:
    def test_meeting_not_found_exits_early(self):
        sid = uuid.uuid4()
        (ms, m, tx, storage, ph, ea, ai_r) = _build_analyze_patches(
            meeting=None, transcripts=[MagicMock(storage_path="/t.txt")]
        )
        mock_loop = MagicMock()
        mock_loop.run_until_complete = MagicMock(side_effect=lambda coro: asyncio.run(coro))
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_sf = MagicMock()
        mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_sf.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_session_repo = AsyncMock()
        mock_session_repo.get_by_id = AsyncMock(return_value=ms)
        mock_meeting_repo = AsyncMock()
        mock_meeting_repo.get_by_id = AsyncMock(return_value=None)

        with patch("asyncio.get_event_loop", return_value=mock_loop), \
             patch("app.core.database.async_session_factory", mock_sf, create=True), \
             patch("app.modules.meetings.repository.MeetingSessionRepository", return_value=mock_session_repo), \
             patch("app.modules.meetings.repository.MeetingRepository", return_value=mock_meeting_repo), \
             patch("app.modules.meetings.repository.MeetingAIAnalysisRepository", return_value=AsyncMock()), \
             patch("app.core.providers.get_storage_service", return_value=AsyncMock()):
            # Should not raise — early return
            analyze_meeting_transcript(str(sid))

        # commit should NOT have been called (early return)
        mock_db.commit.assert_not_called()

    def test_no_transcripts_raises_for_retry(self):
        sid = uuid.uuid4()
        ms = MagicMock(meeting_id=uuid.uuid4())
        mock_meeting = MagicMock(id=uuid.uuid4(), agenda="A")
        mock_loop = MagicMock()
        mock_loop.run_until_complete = MagicMock(side_effect=lambda coro: asyncio.run(coro))
        mock_db = AsyncMock()
        mock_sf = MagicMock()
        mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_sf.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_session_repo = AsyncMock()
        mock_session_repo.get_by_id = AsyncMock(return_value=ms)
        mock_meeting_repo = AsyncMock()
        mock_meeting_repo.get_by_id = AsyncMock(return_value=mock_meeting)
        mock_meeting_repo.list_transcripts_by_session = AsyncMock(return_value=[])

        with patch("asyncio.get_event_loop", return_value=mock_loop), \
             patch("app.core.database.async_session_factory", mock_sf, create=True), \
             patch("app.modules.meetings.repository.MeetingSessionRepository", return_value=mock_session_repo), \
             patch("app.modules.meetings.repository.MeetingRepository", return_value=mock_meeting_repo), \
             patch("app.modules.meetings.repository.MeetingAIAnalysisRepository", return_value=AsyncMock()), \
             patch("app.core.providers.get_storage_service", return_value=AsyncMock()):
            with pytest.raises(Exception, match="Transcript not yet available"):
                analyze_meeting_transcript(str(sid))

    def test_storage_read_failure_propagates(self):
        sid = uuid.uuid4()
        ms = MagicMock(meeting_id=uuid.uuid4())
        mock_meeting = MagicMock(id=uuid.uuid4(), agenda="A")
        tx = MagicMock(storage_path="/tx.txt")
        mock_storage = AsyncMock()
        mock_storage.read = AsyncMock(side_effect=IOError("disk error"))
        mock_loop = MagicMock()
        mock_loop.run_until_complete = MagicMock(side_effect=lambda coro: asyncio.run(coro))
        mock_db = AsyncMock()
        mock_sf = MagicMock()
        mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_sf.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_session_repo = AsyncMock()
        mock_session_repo.get_by_id = AsyncMock(return_value=ms)
        mock_meeting_repo = AsyncMock()
        mock_meeting_repo.get_by_id = AsyncMock(return_value=mock_meeting)
        mock_meeting_repo.list_transcripts_by_session = AsyncMock(return_value=[tx])

        with patch("asyncio.get_event_loop", return_value=mock_loop), \
             patch("app.core.database.async_session_factory", mock_sf, create=True), \
             patch("app.modules.meetings.repository.MeetingSessionRepository", return_value=mock_session_repo), \
             patch("app.modules.meetings.repository.MeetingRepository", return_value=mock_meeting_repo), \
             patch("app.modules.meetings.repository.MeetingAIAnalysisRepository", return_value=AsyncMock()), \
             patch("app.core.providers.get_storage_service", return_value=mock_storage):
            with pytest.raises(IOError):
                analyze_meeting_transcript(str(sid))

    def test_existing_analysis_placeholder_reused(self):
        """If analysis placeholder already exists, it should not create a new one."""
        sid = uuid.uuid4()
        ms = MagicMock(meeting_id=uuid.uuid4())
        mock_meeting = MagicMock(id=uuid.uuid4(), agenda="A")
        tx = MagicMock(storage_path="/tx.txt")
        existing = MagicMock(id=uuid.uuid4())
        mock_storage = AsyncMock()
        mock_storage.read = AsyncMock(return_value=b"")  # empty → mark FAILED
        mock_loop = MagicMock()
        mock_loop.run_until_complete = MagicMock(side_effect=lambda coro: asyncio.run(coro))
        mock_db = AsyncMock()
        mock_sf = MagicMock()
        mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_sf.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_session_repo = AsyncMock()
        mock_session_repo.get_by_id = AsyncMock(return_value=ms)
        mock_meeting_repo = AsyncMock()
        mock_meeting_repo.get_by_id = AsyncMock(return_value=mock_meeting)
        mock_meeting_repo.list_transcripts_by_session = AsyncMock(return_value=[tx])
        mock_ai_repo = AsyncMock()
        mock_ai_repo.get_by_session_id = AsyncMock(return_value=existing)  # already exists
        mock_ai_repo.create_analysis_placeholder = AsyncMock()
        mock_ai_repo.update_status = AsyncMock()
        mock_completion = AsyncMock()

        with patch("asyncio.get_event_loop", return_value=mock_loop), \
             patch("app.core.database.async_session_factory", mock_sf, create=True), \
             patch("app.modules.meetings.repository.MeetingSessionRepository", return_value=mock_session_repo), \
             patch("app.modules.meetings.repository.MeetingRepository", return_value=mock_meeting_repo), \
             patch("app.modules.meetings.repository.MeetingAIAnalysisRepository", return_value=mock_ai_repo), \
             patch("app.modules.meetings.ai_provider_service.AIProviderService", return_value=AsyncMock()), \
             patch("app.modules.meetings.service.MeetingAIAnalysisService", return_value=AsyncMock()), \
             patch("app.modules.meetings.completion_service.MeetingCompletionService", return_value=mock_completion), \
             patch("app.core.providers.get_storage_service", return_value=mock_storage):
            analyze_meeting_transcript(str(sid))

        mock_ai_repo.create_analysis_placeholder.assert_not_called()
        mock_ai_repo.update_status.assert_called_once_with(
            existing.id,
            AIAnalysisStatus.FAILED,
            raw_response={"error": "Transcript file is empty"},
        )

    def test_session_commit_called_on_success(self):
        sid = uuid.uuid4()
        ms = MagicMock(meeting_id=uuid.uuid4())
        mock_meeting = MagicMock(id=uuid.uuid4(), agenda="Agenda")
        tx = MagicMock(storage_path="/tx.txt")
        mock_storage = AsyncMock()
        mock_storage.read = AsyncMock(return_value=b"transcript content")
        mock_loop = MagicMock()
        mock_loop.run_until_complete = MagicMock(side_effect=lambda coro: asyncio.run(coro))
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_sf = MagicMock()
        mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_sf.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_session_repo = AsyncMock()
        mock_session_repo.get_by_id = AsyncMock(return_value=ms)
        mock_meeting_repo = AsyncMock()
        mock_meeting_repo.get_by_id = AsyncMock(return_value=mock_meeting)
        mock_meeting_repo.list_transcripts_by_session = AsyncMock(return_value=[tx])
        mock_ai_repo = AsyncMock()
        mock_ai_repo.get_by_session_id = AsyncMock(return_value=None)
        mock_ai_repo.create_analysis_placeholder = AsyncMock(return_value=MagicMock(id=uuid.uuid4()))
        mock_ai_service = AsyncMock()
        mock_completion = AsyncMock()

        with patch("asyncio.get_event_loop", return_value=mock_loop), \
             patch("app.workers.tasks.AsyncSessionLocal", mock_sf, create=True), \
             patch("app.modules.meetings.repository.MeetingSessionRepository", return_value=mock_session_repo), \
             patch("app.modules.meetings.repository.MeetingRepository", return_value=mock_meeting_repo), \
             patch("app.modules.meetings.repository.MeetingAIAnalysisRepository", return_value=mock_ai_repo), \
             patch("app.modules.meetings.ai_provider_service.AIProviderService", return_value=AsyncMock()), \
             patch("app.modules.meetings.service.MeetingAIAnalysisService", return_value=mock_ai_service), \
             patch("app.modules.meetings.completion_service.MeetingCompletionService", return_value=mock_completion), \
             patch("app.core.providers.get_storage_service", return_value=mock_storage), \
             patch("app.modules.meetings.transcript_preprocessor.preprocess_transcript", return_value="cleaned"):
            analyze_meeting_transcript(str(sid))

        mock_db.commit.assert_called_once()
