import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.meetings.completion_service import MeetingCompletionService
from app.modules.meetings.enums import AIAnalysisStatus
from app.models.meetings import Meeting, MeetingSession, MeetingRecording, MeetingTranscript, MeetingAIAnalysis, MeetingInvitation


def _make_mock_db():
    return AsyncMock()


class TestMeetingCompletionService:
    @pytest.fixture
    def db(self):
        return _make_mock_db()

    @pytest.fixture
    def mock_storage(self):
        storage = MagicMock()
        storage.read = AsyncMock(return_value=b"transcript content")
        return storage

    @pytest.fixture
    def service(self, db, mock_storage):
        return MeetingCompletionService(db, mock_storage)

    def _make_meeting(self, meeting_id=None, host_id=None):
        return MagicMock(
            spec=Meeting,
            id=meeting_id or uuid.UUID("12345678-1234-5678-1234-567812345678"),
            host_id=host_id or uuid.UUID("87654321-4321-8765-4321-876543218765"),
            title="Test Meeting",
            ended_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )

    def _make_session(self, meeting_id=None):
        return MagicMock(
            spec=MeetingSession,
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            meeting_id=meeting_id or uuid.UUID("12345678-1234-5678-1234-567812345678"),
        )

    async def test_send_completion_email_session_not_found(self, service, db):
        db.__class__ = type("Mock", (), {})
        session_repo = MagicMock()
        session_repo.get_by_id = AsyncMock(return_value=None)
        service.session_repo = session_repo

        await service.send_completion_email(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        session_repo.get_by_id.assert_called_once()

    async def test_send_completion_email_meeting_not_found(self, service, db):
        session = self._make_session()
        session_repo = MagicMock()
        session_repo.get_by_id = AsyncMock(return_value=session)
        service.session_repo = session_repo
        service.meeting_repo = MagicMock()
        service.meeting_repo.get_by_id = AsyncMock(return_value=None)

        await service.send_completion_email(session.id)
        service.meeting_repo.get_by_id.assert_called_once_with(session.meeting_id)

    async def test_send_completion_email_no_recipients(self, service, db):
        session = self._make_session()
        meeting = self._make_meeting(meeting_id=session.meeting_id, host_id=session.host_id)
        service.session_repo = MagicMock(get_by_id=AsyncMock(return_value=session))
        service.meeting_repo = MagicMock(
            get_by_id=AsyncMock(return_value=meeting),
            get_user_by_id=AsyncMock(return_value=None),
            list_invitations=AsyncMock(return_value=[]),
            get_participants_by_session=AsyncMock(return_value=[]),
            list_recordings_by_session=AsyncMock(return_value=[]),
            list_transcripts_by_session=AsyncMock(return_value=[]),
        )
        service.ai_repo = MagicMock(get_by_session_id=AsyncMock(return_value=None))

        with patch("app.modules.meetings.completion_service.logger") as mock_logger:
            await service.send_completion_email(session.id)
            mock_logger.warning.assert_called()

    async def test_send_completion_email_dispatches(self, service, db):
        session = self._make_session()
        meeting = self._make_meeting(meeting_id=session.meeting_id, host_id=session.host_id)
        host = MagicMock(email="host@example.com", id=meeting.host_id)
        invitations = [MagicMock(email="invite@example.com", name="Invitee")]
        participants = []
        recordings = []
        transcripts = []
        analysis = None

        service.session_repo = MagicMock(get_by_id=AsyncMock(return_value=session))
        service.meeting_repo = MagicMock(
            get_by_id=AsyncMock(return_value=meeting),
            get_user_by_id=AsyncMock(return_value=host),
            list_invitations=AsyncMock(return_value=invitations),
            get_participants_by_session=AsyncMock(return_value=participants),
            list_recordings_by_session=AsyncMock(return_value=recordings),
            list_transcripts_by_session=AsyncMock(return_value=transcripts),
        )
        service.ai_repo = MagicMock(get_by_session_id=AsyncMock(return_value=analysis))

        with patch("app.workers.tasks.send_html_email") as mock_send:
            await service.send_completion_email(session.id)
            mock_send.delay.assert_called()

    async def test_render_text_body_basic(self, service):
        context = {
            "meeting_title": "Sync",
            "meeting_date": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "frontend_url": "https://example.com",
            "meeting_id": str(uuid.UUID("12345678-1234-5678-1234-567812345678")),
            "has_recording": False,
            "has_transcript": False,
            "has_ai_analysis": False,
        }
        body = service._render_text_body(context)
        assert "Sync" in body
        assert "2026-01-01" in body

    async def test_render_text_body_with_recordings(self, service):
        context = {
            "meeting_title": "Sync",
            "meeting_date": None,
            "frontend_url": "https://example.com",
            "meeting_id": str(uuid.UUID("12345678-1234-5678-1234-567812345678")),
            "has_recording": True,
            "recordings": [{"filename": "rec.webm", "duration": 120.5}],
            "has_transcript": False,
            "has_ai_analysis": False,
        }
        body = service._render_text_body(context)
        assert "Recording:" in body
        assert "rec.webm" in body

    async def test_render_text_body_with_transcripts(self, service):
        context = {
            "meeting_title": "Sync",
            "meeting_date": None,
            "frontend_url": "https://example.com",
            "meeting_id": str(uuid.UUID("12345678-1234-5678-1234-567812345678")),
            "has_recording": False,
            "has_transcript": True,
            "transcripts": [{"filename": "transcript.txt"}],
            "has_ai_analysis": False,
        }
        body = service._render_text_body(context)
        assert "Transcript:" in body
        assert "transcript.txt" in body

    async def test_render_text_body_with_ai_analysis(self, service):
        context = {
            "meeting_title": "Sync",
            "meeting_date": None,
            "frontend_url": "https://example.com",
            "meeting_id": str(uuid.UUID("12345678-1234-5678-1234-567812345678")),
            "has_recording": False,
            "has_transcript": False,
            "has_ai_analysis": True,
            "ai_summary": "Summary text",
            "ai_agenda_coverage": 85,
            "ai_covered_points": ["point1"],
            "ai_out_of_agenda_points": ["point2"],
            "ai_suggested_tasks": [{"title": "Task1", "description": "Desc", "priority": "HIGH"}],
        }
        body = service._render_text_body(context)
        assert "AI Analysis:" in body
        assert "Summary text" in body
        assert "Agenda Coverage: 85%" in body


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _make_db():
    return AsyncMock()


def _make_storage(content=b"transcript content"):
    s = MagicMock()
    s.read = AsyncMock(return_value=content)
    return s


def _make_meeting_obj(meeting_id=None, host_id=None, title="Test Meeting"):
    m = MagicMock(spec=Meeting)
    m.id = meeting_id or uuid.uuid4()
    m.host_id = host_id or uuid.uuid4()
    m.title = title
    m.ended_at = datetime.now(timezone.utc)
    m.created_at = datetime.now(timezone.utc)
    return m


def _make_session_obj(meeting_id=None):
    s = MagicMock(spec=MeetingSession)
    s.id = uuid.uuid4()
    s.meeting_id = meeting_id or uuid.uuid4()
    return s


def _make_recording_obj(filename="rec.webm"):
    r = MagicMock()
    r.filename = filename
    r.size = 1024
    r.duration = 60.0
    r.content_type = "audio/webm"
    r.storage_path = f"/tmp/{filename}"
    return r


def _make_transcript_obj(filename="tx.txt"):
    t = MagicMock()
    t.filename = filename
    t.size = 512
    t.content_type = "text/plain"
    t.storage_path = f"/tmp/{filename}"
    return t


def _make_analysis_obj(status=AIAnalysisStatus.COMPLETED):
    a = MagicMock()
    a.status = status
    a.summary = "Good meeting"
    a.agenda_coverage_percentage = 90
    a.covered_points = ["point A", "point B"]
    a.out_of_agenda_points = ["off topic"]
    a.suggested_tasks = [{"title": "Follow up", "description": "Do it", "priority": "HIGH"}]
    return a


@pytest.fixture
def svc():
    return MeetingCompletionService(_make_db(), _make_storage())


# ── _build_recipient_list ──────────────────────────────────────────────────────

class TestBuildRecipientList:
    async def test_host_added_first(self, svc):
        host = MagicMock(email="host@example.com")
        recipients = await svc._build_recipient_list(host, [], [])
        assert recipients[0] == "host@example.com"

    async def test_no_host_skipped(self, svc):
        recipients = await svc._build_recipient_list(None, [], [])
        assert recipients == []

    async def test_host_without_email_skipped(self, svc):
        host = MagicMock(email=None)
        recipients = await svc._build_recipient_list(host, [], [])
        assert recipients == []

    async def test_invitation_emails_added(self, svc):
        host = MagicMock(email="host@example.com")
        inv = MagicMock(email="invitee@example.com")
        recipients = await svc._build_recipient_list(host, [inv], [])
        assert "invitee@example.com" in recipients

    async def test_duplicate_emails_deduplicated(self, svc):
        host = MagicMock(email="host@example.com")
        inv = MagicMock(email="host@example.com")
        recipients = await svc._build_recipient_list(host, [inv], [])
        assert recipients.count("host@example.com") == 1

    async def test_guest_participant_email_added(self, svc):
        p = MagicMock(user_id=None, guest_email="guest@example.com")
        recipients = await svc._build_recipient_list(None, [], [p])
        assert "guest@example.com" in recipients

    async def test_registered_participant_email_fetched(self, svc):
        user_id = uuid.uuid4()
        p = MagicMock(user_id=user_id, guest_email=None)
        user = MagicMock(email="registered@example.com")
        svc.meeting_repo = MagicMock()
        svc.meeting_repo.get_user_by_id = AsyncMock(return_value=user)
        recipients = await svc._build_recipient_list(None, [], [p])
        assert "registered@example.com" in recipients

    async def test_registered_participant_user_not_found_skipped(self, svc):
        user_id = uuid.uuid4()
        p = MagicMock(user_id=user_id, guest_email=None)
        svc.meeting_repo = MagicMock()
        svc.meeting_repo.get_user_by_id = AsyncMock(return_value=None)
        recipients = await svc._build_recipient_list(None, [], [p])
        assert recipients == []

    async def test_multiple_invitations_all_added(self, svc):
        invs = [MagicMock(email=f"inv{i}@example.com") for i in range(3)]
        recipients = await svc._build_recipient_list(None, invs, [])
        assert len(recipients) == 3

    async def test_invitation_without_email_skipped(self, svc):
        inv = MagicMock(email=None)
        recipients = await svc._build_recipient_list(None, [inv], [])
        assert recipients == []


# ── _build_email_context ──────────────────────────────────────────────────────

class TestBuildEmailContext:
    def test_context_contains_meeting_title(self, svc):
        meeting = _make_meeting_obj(title="My Meeting")
        ctx = svc._build_email_context(meeting, [], [], None)
        assert ctx["meeting_title"] == "My Meeting"

    def test_context_has_meeting_id_as_string(self, svc):
        meeting = _make_meeting_obj()
        ctx = svc._build_email_context(meeting, [], [], None)
        assert ctx["meeting_id"] == str(meeting.id)

    def test_context_no_recording_flag(self, svc):
        ctx = svc._build_email_context(_make_meeting_obj(), [], [], None)
        assert ctx["has_recording"] is False

    def test_context_no_transcript_flag(self, svc):
        ctx = svc._build_email_context(_make_meeting_obj(), [], [], None)
        assert ctx["has_transcript"] is False

    def test_context_no_ai_analysis_flag(self, svc):
        ctx = svc._build_email_context(_make_meeting_obj(), [], [], None)
        assert ctx["has_ai_analysis"] is False

    def test_context_with_recording(self, svc):
        rec = _make_recording_obj()
        ctx = svc._build_email_context(_make_meeting_obj(), [rec], [], None)
        assert ctx["has_recording"] is True
        assert len(ctx["recordings"]) == 1
        assert ctx["recordings"][0]["filename"] == "rec.webm"

    def test_context_with_transcript(self, svc):
        tx = _make_transcript_obj()
        ctx = svc._build_email_context(_make_meeting_obj(), [], [tx], None)
        assert ctx["has_transcript"] is True
        assert ctx["transcripts"][0]["filename"] == "tx.txt"

    def test_context_with_completed_ai_analysis(self, svc):
        analysis = _make_analysis_obj(status=AIAnalysisStatus.COMPLETED)
        ctx = svc._build_email_context(_make_meeting_obj(), [], [], analysis)
        assert ctx["has_ai_analysis"] is True
        assert ctx["ai_summary"] == "Good meeting"
        assert ctx["ai_agenda_coverage"] == 90

    def test_context_with_pending_ai_analysis_excluded(self, svc):
        analysis = _make_analysis_obj(status=AIAnalysisStatus.PENDING)
        ctx = svc._build_email_context(_make_meeting_obj(), [], [], analysis)
        assert ctx["has_ai_analysis"] is False

    def test_context_with_failed_ai_analysis_excluded(self, svc):
        analysis = _make_analysis_obj(status=AIAnalysisStatus.FAILED)
        ctx = svc._build_email_context(_make_meeting_obj(), [], [], analysis)
        assert ctx["has_ai_analysis"] is False

    def test_context_uses_ended_at_if_present(self, svc):
        meeting = _make_meeting_obj()
        ended = datetime(2026, 6, 1, tzinfo=timezone.utc)
        meeting.ended_at = ended
        ctx = svc._build_email_context(meeting, [], [], None)
        assert ctx["meeting_date"] == ended

    def test_context_falls_back_to_created_at_if_no_ended_at(self, svc):
        meeting = _make_meeting_obj()
        created = datetime(2026, 5, 1, tzinfo=timezone.utc)
        meeting.ended_at = None
        meeting.created_at = created
        ctx = svc._build_email_context(meeting, [], [], None)
        assert ctx["meeting_date"] == created

    def test_context_multiple_recordings(self, svc):
        recs = [_make_recording_obj(f"rec{i}.webm") for i in range(3)]
        ctx = svc._build_email_context(_make_meeting_obj(), recs, [], None)
        assert len(ctx["recordings"]) == 3

    def test_context_multiple_transcripts(self, svc):
        txs = [_make_transcript_obj(f"tx{i}.txt") for i in range(2)]
        ctx = svc._build_email_context(_make_meeting_obj(), [], txs, None)
        assert len(ctx["transcripts"]) == 2


# ── _build_attachments ─────────────────────────────────────────────────────────

class TestBuildAttachments:
    async def test_transcript_attachment_included(self, svc):
        tx = _make_transcript_obj()
        svc.storage = _make_storage(b"transcript bytes")
        attachments = await svc._build_attachments([tx], [])
        assert len(attachments) == 1
        assert attachments[0]["filename"] == "tx.txt"
        assert attachments[0]["content"] == b"transcript bytes"

    async def test_recording_attachment_included(self, svc):
        rec = _make_recording_obj()
        svc.storage = _make_storage(b"recording bytes")
        attachments = await svc._build_attachments([], [rec])
        assert len(attachments) == 1
        assert attachments[0]["filename"] == "rec.webm"

    async def test_both_transcript_and_recording_included(self, svc):
        tx = _make_transcript_obj()
        rec = _make_recording_obj()
        svc.storage = _make_storage(b"bytes")
        attachments = await svc._build_attachments([tx], [rec])
        assert len(attachments) == 2

    async def test_storage_read_failure_skips_attachment(self, svc):
        tx = _make_transcript_obj()
        svc.storage = MagicMock()
        svc.storage.read = AsyncMock(side_effect=Exception("file missing"))
        attachments = await svc._build_attachments([tx], [])
        assert attachments == []

    async def test_multiple_transcripts_all_attached(self, svc):
        txs = [_make_transcript_obj(f"tx{i}.txt") for i in range(3)]
        svc.storage = _make_storage(b"data")
        attachments = await svc._build_attachments(txs, [])
        assert len(attachments) == 3

    async def test_partial_failure_skips_only_failing(self, svc):
        tx_ok = _make_transcript_obj("ok.txt")
        tx_bad = _make_transcript_obj("bad.txt")

        async def read_side_effect(path):
            if "bad" in path:
                raise Exception("fail")
            return b"ok content"

        svc.storage = MagicMock()
        svc.storage.read = AsyncMock(side_effect=read_side_effect)
        attachments = await svc._build_attachments([tx_ok, tx_bad], [])
        assert len(attachments) == 1
        assert attachments[0]["filename"] == "ok.txt"


# ── _dispatch_emails ───────────────────────────────────────────────────────────

class TestDispatchEmails:
    def test_dispatch_calls_delay_for_each_recipient(self, svc):
        recipients = ["a@example.com", "b@example.com", "c@example.com"]
        ctx = {
            "meeting_title": "Test",
            "meeting_date": None,
            "frontend_url": "https://example.com",
            "meeting_id": str(uuid.uuid4()),
            "has_recording": False,
            "has_transcript": False,
            "has_ai_analysis": False,
        }
        with patch("app.workers.tasks.send_html_email") as mock_task:
            svc._dispatch_emails(ctx, recipients, [])
        assert mock_task.delay.call_count == 3

    def test_dispatch_subject_contains_meeting_title(self, svc):
        ctx = {
            "meeting_title": "My Important Meeting",
            "meeting_date": None,
            "frontend_url": "https://example.com",
            "meeting_id": str(uuid.uuid4()),
            "has_recording": False,
            "has_transcript": False,
            "has_ai_analysis": False,
        }
        with patch("app.workers.tasks.send_html_email") as mock_task:
            svc._dispatch_emails(ctx, ["a@example.com"], [])
        call_kwargs = mock_task.delay.call_args[1]
        assert "My Important Meeting" in call_kwargs["subject"]

    def test_dispatch_exception_per_recipient_does_not_crash(self, svc):
        ctx = {
            "meeting_title": "Test",
            "meeting_date": None,
            "frontend_url": "https://example.com",
            "meeting_id": str(uuid.uuid4()),
            "has_recording": False,
            "has_transcript": False,
            "has_ai_analysis": False,
        }
        with patch("app.workers.tasks.send_html_email") as mock_task:
            mock_task.delay.side_effect = Exception("queue down")
            svc._dispatch_emails(ctx, ["a@example.com", "b@example.com"], [])

    def test_dispatch_passes_attachments(self, svc):
        ctx = {
            "meeting_title": "T",
            "meeting_date": None,
            "frontend_url": "https://x.com",
            "meeting_id": str(uuid.uuid4()),
            "has_recording": False,
            "has_transcript": False,
            "has_ai_analysis": False,
        }
        attachments = [{"filename": "tx.txt", "content": b"data", "content_type": "text/plain"}]
        with patch("app.workers.tasks.send_html_email") as mock_task:
            svc._dispatch_emails(ctx, ["a@example.com"], attachments)
        call_kwargs = mock_task.delay.call_args[1]
        assert call_kwargs["attachments"] == attachments

    def test_dispatch_empty_recipients_sends_nothing(self, svc):
        ctx = {
            "meeting_title": "T",
            "meeting_date": None,
            "frontend_url": "https://x.com",
            "meeting_id": str(uuid.uuid4()),
            "has_recording": False,
            "has_transcript": False,
            "has_ai_analysis": False,
        }
        with patch("app.workers.tasks.send_html_email") as mock_task:
            svc._dispatch_emails(ctx, [], [])
        mock_task.delay.assert_not_called()


# ── _render_text_body — edge cases ─────────────────────────────────────────────

class TestRenderTextBodyEdgeCases:
    def test_none_date_omitted(self, svc):
        ctx = {
            "meeting_title": "T",
            "meeting_date": None,
            "frontend_url": "https://x.com",
            "meeting_id": str(uuid.uuid4()),
            "has_recording": False,
            "has_transcript": False,
            "has_ai_analysis": False,
        }
        body = svc._render_text_body(ctx)
        assert "Date:" not in body

    def test_non_datetime_date_shown_as_string(self, svc):
        ctx = {
            "meeting_title": "T",
            "meeting_date": "2026-01-01",
            "frontend_url": "https://x.com",
            "meeting_id": str(uuid.uuid4()),
            "has_recording": False,
            "has_transcript": False,
            "has_ai_analysis": False,
        }
        body = svc._render_text_body(ctx)
        assert "2026-01-01" in body

    def test_recording_without_duration_no_duration_str(self, svc):
        ctx = {
            "meeting_title": "T",
            "meeting_date": None,
            "frontend_url": "https://x.com",
            "meeting_id": str(uuid.uuid4()),
            "has_recording": True,
            "recordings": [{"filename": "rec.webm"}],
            "has_transcript": False,
            "has_ai_analysis": False,
        }
        body = svc._render_text_body(ctx)
        assert "rec.webm" in body
        assert "(s)" not in body

    def test_ai_covered_points_rendered(self, svc):
        ctx = {
            "meeting_title": "T",
            "meeting_date": None,
            "frontend_url": "https://x.com",
            "meeting_id": str(uuid.uuid4()),
            "has_recording": False,
            "has_transcript": False,
            "has_ai_analysis": True,
            "ai_summary": None,
            "ai_agenda_coverage": None,
            "ai_covered_points": ["covered item"],
            "ai_out_of_agenda_points": [],
            "ai_suggested_tasks": [],
        }
        body = svc._render_text_body(ctx)
        assert "covered item" in body

    def test_ai_out_of_agenda_rendered(self, svc):
        ctx = {
            "meeting_title": "T",
            "meeting_date": None,
            "frontend_url": "https://x.com",
            "meeting_id": str(uuid.uuid4()),
            "has_recording": False,
            "has_transcript": False,
            "has_ai_analysis": True,
            "ai_summary": None,
            "ai_agenda_coverage": None,
            "ai_covered_points": [],
            "ai_out_of_agenda_points": ["unexpected topic"],
            "ai_suggested_tasks": [],
        }
        body = svc._render_text_body(ctx)
        assert "unexpected topic" in body

    def test_ai_suggested_tasks_rendered(self, svc):
        ctx = {
            "meeting_title": "T",
            "meeting_date": None,
            "frontend_url": "https://x.com",
            "meeting_id": str(uuid.uuid4()),
            "has_recording": False,
            "has_transcript": False,
            "has_ai_analysis": True,
            "ai_summary": None,
            "ai_agenda_coverage": None,
            "ai_covered_points": [],
            "ai_out_of_agenda_points": [],
            "ai_suggested_tasks": [{"title": "Finish report", "description": "ASAP", "priority": "HIGH"}],
        }
        body = svc._render_text_body(ctx)
        assert "Finish report" in body

    def test_view_meeting_link_always_present(self, svc):
        ctx = {
            "meeting_title": "T",
            "meeting_date": None,
            "frontend_url": "https://example.com",
            "meeting_id": "some-id",
            "has_recording": False,
            "has_transcript": False,
            "has_ai_analysis": False,
        }
        body = svc._render_text_body(ctx)
        assert "https://example.com/meetings/some-id" in body


# ── send_completion_email — full pipeline ──────────────────────────────────────

class TestSendCompletionEmailFullPipeline:
    def _wire_service(self, service, session, meeting, host, invitations,
                      participants, recordings, transcripts, analysis):
        service.session_repo = MagicMock(get_by_id=AsyncMock(return_value=session))
        service.meeting_repo = MagicMock(
            get_by_id=AsyncMock(return_value=meeting),
            get_user_by_id=AsyncMock(return_value=host),
            list_invitations=AsyncMock(return_value=invitations),
            get_participants_by_session=AsyncMock(return_value=participants),
            list_recordings_by_session=AsyncMock(return_value=recordings),
            list_transcripts_by_session=AsyncMock(return_value=transcripts),
        )
        service.ai_repo = MagicMock(get_by_session_id=AsyncMock(return_value=analysis))

    async def test_full_pipeline_multiple_recipients(self):
        db, storage = _make_db(), _make_storage()
        service = MeetingCompletionService(db, storage)
        session = _make_session_obj()
        meeting = _make_meeting_obj(meeting_id=session.meeting_id)
        host = MagicMock(email="host@example.com")
        inv1 = MagicMock(email="inv1@example.com")
        inv2 = MagicMock(email="inv2@example.com")
        self._wire_service(service, session, meeting, host, [inv1, inv2], [], [], [], None)
        with patch("app.workers.tasks.send_html_email") as mock_task:
            await service.send_completion_email(session.id)
        assert mock_task.delay.call_count == 3

    async def test_full_pipeline_with_ai_analysis(self):
        db, storage = _make_db(), _make_storage(b"tx content")
        service = MeetingCompletionService(db, storage)
        session = _make_session_obj()
        meeting = _make_meeting_obj(meeting_id=session.meeting_id)
        host = MagicMock(email="host@example.com")
        analysis = _make_analysis_obj(status=AIAnalysisStatus.COMPLETED)
        tx = _make_transcript_obj()
        self._wire_service(service, session, meeting, host, [], [], [], [tx], analysis)
        with patch("app.workers.tasks.send_html_email") as mock_task:
            await service.send_completion_email(session.id)
        mock_task.delay.assert_called_once()
        call_kwargs = mock_task.delay.call_args[1]
        assert "Good meeting" in call_kwargs["text_body"]

    async def test_full_pipeline_with_multiple_recordings(self):
        db, storage = _make_db(), _make_storage(b"bytes")
        service = MeetingCompletionService(db, storage)
        session = _make_session_obj()
        meeting = _make_meeting_obj(meeting_id=session.meeting_id)
        host = MagicMock(email="host@example.com")
        recs = [_make_recording_obj(f"rec{i}.webm") for i in range(2)]
        self._wire_service(service, session, meeting, host, [], [], recs, [], None)
        with patch("app.workers.tasks.send_html_email") as mock_task:
            await service.send_completion_email(session.id)
        call_kwargs = mock_task.delay.call_args[1]
        assert "rec0.webm" in call_kwargs["text_body"]
        assert "rec1.webm" in call_kwargs["text_body"]
