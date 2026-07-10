import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from app.modules.meetings.repository import (
    MeetingRepository,
    MeetingAIAnalysisRepository,
    MeetingSessionRepository,
)
from app.modules.meetings.enums import (
    MeetingStatus,
    ParticipantType,
    ParticipantStatus,
    MeetingType,
    SessionStatus,
    AIAnalysisStatus,
)
from app.models.meetings import (
    Meeting,
    MeetingInvitation,
    MeetingParticipant,
    MeetingRecording,
    MeetingTranscript,
    MeetingAIAnalysis,
    MeetingSession,
)


def _make_mock_db():
    return AsyncMock()


def _mock_execute_return(value):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = value
    mock_result.scalars.return_value.all.return_value = value if isinstance(value, list) else [value]
    mock_result.scalar.return_value = value if not isinstance(value, list) else len(value)
    mock_result.all.return_value = value if isinstance(value, list) else [value]
    return mock_result


class TestMeetingRepository:
    @pytest.fixture
    def db(self):
        return _make_mock_db()

    @pytest.fixture
    def repo(self, db):
        return MeetingRepository(db)

    def test_generate_meeting_code_format(self, repo):
        code = repo.generate_meeting_code()
        parts = code.split("-")
        assert len(parts) >= 3
        assert all(len(p) <= 4 for p in parts)
        assert code.islower()

    def test_generate_meeting_code_unique(self, repo):
        codes = {repo.generate_meeting_code() for _ in range(20)}
        assert len(codes) > 1

    async def test_create(self, repo, db):
        host_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        db.execute.return_value = _mock_execute_return(None)
        meeting = await repo.create(host_id, {"title": "New Meeting"})
        assert meeting.title == "New Meeting"
        db.add.assert_called()
        db.flush.assert_called()

    async def test_create_rollback_on_exception(self, repo, db):
        db.flush.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.create(uuid.uuid4(), {"title": "Fail"})
        db.rollback.assert_called()

    async def test_get_by_id(self, repo, db):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_meeting = MagicMock(spec=Meeting)
        db.execute.return_value = _mock_execute_return(mock_meeting)
        result = await repo.get_by_id(meeting_id)
        assert result == mock_meeting

    async def test_get_by_id_excludes_deleted_by_default(self, repo, db):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        await repo.get_by_id(meeting_id)
        stmt = db.execute.call_args[0][0]
        assert "deleted_at IS NULL" in str(stmt)

    async def test_get_by_id_includes_deleted(self, repo, db):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        await repo.get_by_id(meeting_id, include_deleted=True)
        db.execute.assert_called()

    async def test_get_by_code_case_insensitive(self, repo, db):
        mock_meeting = MagicMock(spec=Meeting)
        db.execute.return_value = _mock_execute_return(mock_meeting)
        result = await repo.get_by_code("ABC-DEFG-HIJ")
        assert result == mock_meeting

    async def test_get_by_code_strips_whitespace(self, repo, db):
        mock_meeting = MagicMock(spec=Meeting)
        db.execute.return_value = _mock_execute_return(mock_meeting)
        result = await repo.get_by_code("  abc-defg-hij  ")
        assert result == mock_meeting

    async def test_update(self, repo, db):
        mock_meeting = MagicMock(spec=Meeting)
        db.execute.return_value = _mock_execute_return(mock_meeting)
        result = await repo.update(mock_meeting, {"title": "Updated"})
        assert result == mock_meeting
        db.add.assert_called()
        db.flush.assert_called()

    async def test_update_rollback_on_exception(self, repo, db):
        mock_meeting = MagicMock(spec=Meeting)
        db.flush.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.update(mock_meeting, {"title": "Updated"})
        db.rollback.assert_called()

    async def test_list_user_meetings(self, repo, db):
        mock_meetings = [MagicMock(spec=Meeting), MagicMock(spec=Meeting)]
        db.execute.return_value = _mock_execute_return(mock_meetings)
        result = await repo.list_user_meetings(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert len(result) == 2

    async def test_create_participant(self, repo, db):
        session_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        db.execute.return_value = _mock_execute_return(None)
        participant = await repo.create_participant(
            session_id=session_id,
            user_id=None,
            guest_name="Guest",
            guest_email="guest@example.com",
            p_type=ParticipantType.GUEST,
            status=ParticipantStatus.WAITING,
        )
        db.add.assert_called()
        assert participant.guest_name == "Guest"

    async def test_create_participant_rollback_on_exception(self, repo, db):
        db.flush.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.create_participant(
                uuid.UUID("12345678-1234-5678-1234-567812345678"),
                None,
                "Guest",
                "guest@example.com",
                ParticipantType.GUEST,
                ParticipantStatus.WAITING,
            )
        db.rollback.assert_called()

    async def test_get_participant_by_id(self, repo, db):
        participant_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_p = MagicMock(spec=MeetingParticipant)
        db.execute.return_value = _mock_execute_return(mock_p)
        result = await repo.get_participant_by_id(participant_id)
        assert result == mock_p

    async def test_get_active_participant_by_user_id(self, repo, db):
        session_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        mock_p = MagicMock(spec=MeetingParticipant)
        db.execute.return_value = _mock_execute_return(mock_p)
        result = await repo.get_active_participant(session_id, user_id=user_id)
        assert result == mock_p

    async def test_get_active_participant_returns_none_without_identifiers(self, repo, db):
        result = await repo.get_active_participant(uuid.uuid4())
        assert result is None
        db.execute.assert_not_called()

    async def test_get_last_participant(self, repo, db):
        session_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        mock_p = MagicMock(spec=MeetingParticipant)
        db.execute.return_value = _mock_execute_return(mock_p)
        result = await repo.get_last_participant(session_id, user_id=user_id)
        assert result == mock_p

    async def test_get_participants_by_session(self, repo, db):
        session_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_p = MagicMock(spec=MeetingParticipant)
        db.execute.return_value = MagicMock()
        db.execute.return_value.all.return_value = [(mock_p, "Alice")]
        result = await repo.get_participants_by_session(session_id)
        assert len(result) == 1
        assert result[0] == mock_p

    async def test_get_participants_by_meeting(self, repo, db):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_p = MagicMock(spec=MeetingParticipant)
        db.execute.return_value = MagicMock()
        db.execute.return_value.all.return_value = [(mock_p, "Bob")]
        result = await repo.get_participants_by_meeting(meeting_id)
        assert len(result) == 1

    async def test_add_recording(self, repo, db):
        db.execute.return_value = _mock_execute_return(None)
        rec = await repo.add_recording({
            "session_id": uuid.UUID("12345678-1234-5678-1234-567812345678"),
            "filename": "rec.webm",
            "content_type": "audio/webm",
            "size": 1024,
            "storage_path": "/tmp/rec.webm",
        })
        db.add.assert_called()
        assert rec.filename == "rec.webm"

    async def test_add_transcript(self, repo, db):
        db.execute.return_value = _mock_execute_return(None)
        tx = await repo.add_transcript({
            "session_id": uuid.UUID("12345678-1234-5678-1234-567812345678"),
            "filename": "transcript.txt",
            "content_type": "text/plain",
            "size": 2048,
            "storage_path": "/tmp/tx.txt",
        })
        db.add.assert_called()
        assert tx.filename == "transcript.txt"

    async def test_get_recording_by_id(self, repo, db):
        rec_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_rec = MagicMock(spec=MeetingRecording)
        db.execute.return_value = _mock_execute_return(mock_rec)
        result = await repo.get_recording_by_id(rec_id)
        assert result == mock_rec

    async def test_get_transcript_by_id(self, repo, db):
        tx_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_tx = MagicMock(spec=MeetingTranscript)
        db.execute.return_value = _mock_execute_return(mock_tx)
        result = await repo.get_transcript_by_id(tx_id)
        assert result == mock_tx

    async def test_list_recordings_by_session(self, repo, db):
        session_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_recs = [MagicMock(spec=MeetingRecording)]
        db.execute.return_value = _mock_execute_return(mock_recs)
        result = await repo.list_recordings_by_session(session_id)
        assert len(result) == 1

    async def test_list_transcripts_by_session(self, repo, db):
        session_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_txs = [MagicMock(spec=MeetingTranscript)]
        db.execute.return_value = _mock_execute_return(mock_txs)
        result = await repo.list_transcripts_by_session(session_id)
        assert len(result) == 1

    async def test_list_recordings_by_meeting(self, repo, db):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_recs = [MagicMock(spec=MeetingRecording)]
        db.execute.return_value = _mock_execute_return(mock_recs)
        result = await repo.list_recordings_by_meeting(meeting_id)
        assert len(result) == 1

    async def test_list_transcripts_by_meeting(self, repo, db):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_txs = [MagicMock(spec=MeetingTranscript)]
        db.execute.return_value = _mock_execute_return(mock_txs)
        result = await repo.list_transcripts_by_meeting(meeting_id)
        assert len(result) == 1

    async def test_delete_recording_meta(self, repo, db):
        rec = MagicMock(spec=MeetingRecording)
        await repo.delete_recording_meta(rec)
        db.delete.assert_called_with(rec)
        db.flush.assert_called()

    async def test_delete_transcript_meta(self, repo, db):
        tx = MagicMock(spec=MeetingTranscript)
        await repo.delete_transcript_meta(tx)
        db.delete.assert_called_with(tx)
        db.flush.assert_called()

    async def test_update_participant(self, repo, db):
        mock_p = MagicMock(spec=MeetingParticipant)
        db.execute.return_value = _mock_execute_return(mock_p)
        result = await repo.update_participant(mock_p, {"is_muted": True})
        assert result == mock_p

    async def test_soft_delete(self, repo, db):
        now = datetime.now(timezone.utc)
        mock_meeting = MagicMock(spec=Meeting)
        await repo.soft_delete(mock_meeting)
        assert mock_meeting.deleted_at is not None

    async def test_restore(self, repo, db):
        mock_meeting = MagicMock(spec=Meeting)
        result = await repo.restore(mock_meeting)
        assert result.deleted_at is None
        db.add.assert_called()
        db.flush.assert_called()

    async def test_get_meeting_status(self, repo, db):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        db.execute.return_value = _mock_execute_return(MeetingStatus.ACTIVE)
        result = await repo.get_meeting_status(meeting_id)
        assert result == MeetingStatus.ACTIVE

    async def test_create_invitation(self, repo, db):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        db.execute.return_value = _mock_execute_return(None)
        inv = await repo.create_invitation(meeting_id, {"name": "John", "email": "john@example.com"})
        db.add.assert_called()
        assert inv.name == "John"

    async def test_get_invitation_by_email_case_insensitive(self, repo, db):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_inv = MagicMock(spec=MeetingInvitation)
        db.execute.return_value = _mock_execute_return(mock_inv)
        result = await repo.get_invitation_by_email(meeting_id, "John@Example.COM")
        assert result == mock_inv

    async def test_count_invitations(self, repo, db):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        db.execute.return_value = _mock_execute_return(3)
        result = await repo.count_invitations(meeting_id)
        assert result == 3

    async def test_get_user_by_id(self, repo, db):
        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user = MagicMock()
        mock_user.id = user_id
        db.execute.return_value = _mock_execute_return(mock_user)
        result = await repo.get_user_by_id(user_id)
        assert result == mock_user

    async def test_list_invitations(self, repo, db):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_invs = [MagicMock(spec=MeetingInvitation)]
        db.execute.return_value = _mock_execute_return(mock_invs)
        result = await repo.list_invitations(meeting_id)
        assert len(result) == 1

    async def test_get_participants_by_session_ids(self, repo, db):
        session_ids = {uuid.UUID("12345678-1234-5678-1234-567812345678")}
        mock_p = MagicMock(spec=MeetingParticipant)
        db.execute.return_value = MagicMock()
        db.execute.return_value.all.return_value = [(mock_p, "Alice")]
        result = await repo.get_participants_by_session_ids(session_ids)
        assert len(result) == 1

    async def test_get_sessions_for_user(self, repo, db):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        mock_sessions = [MagicMock(spec=MeetingSession)]
        db.execute.return_value = _mock_execute_return(mock_sessions)
        result = await repo.get_sessions_for_user(meeting_id, user_id)
        assert len(result) == 1

    async def test_get_session_by_recording_id(self, repo, db):
        rec_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_session = MagicMock(spec=MeetingSession)
        db.execute.return_value = _mock_execute_return(mock_session)
        result = await repo.get_session_by_recording_id(rec_id)
        assert result == mock_session

    async def test_get_session_by_transcript_id(self, repo, db):
        tx_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_session = MagicMock(spec=MeetingSession)
        db.execute.return_value = _mock_execute_return(mock_session)
        result = await repo.get_session_by_transcript_id(tx_id)
        assert result == mock_session

    async def test_get_meeting_by_recording_id(self, repo, db):
        rec_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_meeting = MagicMock(spec=Meeting)
        db.execute.return_value = _mock_execute_return(mock_meeting)
        result = await repo.get_meeting_by_recording_id(rec_id)
        assert result == mock_meeting

    async def test_get_meeting_by_transcript_id(self, repo, db):
        tx_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_meeting = MagicMock(spec=Meeting)
        db.execute.return_value = _mock_execute_return(mock_meeting)
        result = await repo.get_meeting_by_transcript_id(tx_id)
        assert result == mock_meeting

    async def test_list_recordings_by_session_ids(self, repo, db):
        session_ids = {uuid.UUID("12345678-1234-5678-1234-567812345678")}
        mock_recs = [MagicMock(spec=MeetingRecording)]
        db.execute.return_value = _mock_execute_return(mock_recs)
        result = await repo.list_recordings_by_session_ids(session_ids)
        assert len(result) == 1

    async def test_list_transcripts_by_session_ids(self, repo, db):
        session_ids = {uuid.UUID("12345678-1234-5678-1234-567812345678")}
        mock_txs = [MagicMock(spec=MeetingTranscript)]
        db.execute.return_value = _mock_execute_return(mock_txs)
        result = await repo.list_transcripts_by_session_ids(session_ids)
        assert len(result) == 1


class TestMeetingAIAnalysisRepository:
    @pytest.fixture
    def db(self):
        return _make_mock_db()

    @pytest.fixture
    def repo(self, db):
        return MeetingAIAnalysisRepository(db)

    async def test_create_analysis_placeholder(self, repo, db):
        db.execute.return_value = _mock_execute_return(None)
        analysis = await repo.create_analysis_placeholder(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        db.add.assert_called()
        assert analysis.status == AIAnalysisStatus.PENDING

    async def test_get_by_session_id(self, repo, db):
        session_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_analysis = MagicMock(spec=MeetingAIAnalysis)
        db.execute.return_value = _mock_execute_return(mock_analysis)
        result = await repo.get_by_session_id(session_id)
        assert result == mock_analysis

    async def test_get_by_meeting_id(self, repo, db):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_analysis = MagicMock(spec=MeetingAIAnalysis)
        db.execute.return_value = _mock_execute_return(mock_analysis)
        result = await repo.get_by_meeting_id(meeting_id)
        assert result == mock_analysis

    async def test_list_recent_for_user(self, repo, db):
        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        rows = [
            (
                uuid.UUID("12345678-1234-5678-1234-567812345678"),
                uuid.UUID("87654321-4321-8765-4321-876543218765"),
                AIAnalysisStatus.COMPLETED,
                "Summary",
                85,
                datetime.now(timezone.utc),
                datetime.now(timezone.utc),
                uuid.UUID("11111111-1111-1111-1111-111111111111"),
                "Meeting Title",
                datetime.now(timezone.utc),
            )
        ]
        db.execute.return_value = MagicMock()
        db.execute.return_value.all.return_value = rows
        result = await repo.list_recent_for_user(user_id, limit=5)
        assert len(result) == 1

    async def test_update_status_processing(self, repo, db):
        analysis_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        db.execute.return_value = _mock_execute_return(None)
        await repo.update_status(analysis_id, AIAnalysisStatus.PROCESSING)
        db.execute.assert_called()
        db.flush.assert_called()

    async def test_update_status_completed_sets_completed_at(self, repo, db):
        analysis_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        db.execute.return_value = _mock_execute_return(None)
        await repo.update_status(analysis_id, AIAnalysisStatus.COMPLETED, summary="Done")
        db.execute.assert_called()
        db.flush.assert_called()

    async def test_update_status_failed_sets_completed_at(self, repo, db):
        analysis_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        db.execute.return_value = _mock_execute_return(None)
        await repo.update_status(analysis_id, AIAnalysisStatus.FAILED)
        db.execute.assert_called()
        db.flush.assert_called()


class TestMeetingSessionRepository:
    @pytest.fixture
    def db(self):
        return _make_mock_db()

    @pytest.fixture
    def repo(self, db):
        return MeetingSessionRepository(db)

    async def test_create_session(self, repo, db):
        db.execute.return_value = _mock_execute_return(None)
        session = await repo.create_session(
            uuid.UUID("12345678-1234-5678-1234-567812345678"),
            uuid.UUID("87654321-4321-8765-4321-876543218765"),
        )
        db.add.assert_called()
        assert session.status == SessionStatus.ACTIVE

    async def test_get_by_id(self, repo, db):
        session_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_session = MagicMock(spec=MeetingSession)
        db.execute.return_value = _mock_execute_return(mock_session)
        result = await repo.get_by_id(session_id)
        assert result == mock_session

    async def test_get_active_session(self, repo, db):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_session = MagicMock(spec=MeetingSession)
        db.execute.return_value = _mock_execute_return(mock_session)
        result = await repo.get_active_session(meeting_id)
        assert result == mock_session

    async def test_get_sessions_for_meeting(self, repo, db):
        meeting_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_sessions = [MagicMock(spec=MeetingSession)]
        db.execute.return_value = _mock_execute_return(mock_sessions)
        result = await repo.get_sessions_for_meeting(meeting_id)
        assert len(result) == 1

    async def test_update(self, repo, db):
        mock_session = MagicMock(spec=MeetingSession)
        db.execute.return_value = _mock_execute_return(mock_session)
        result = await repo.update(mock_session, {"status": SessionStatus.ENDED})
        assert result == mock_session
        db.add.assert_called()
        db.flush.assert_called()

    async def test_update_rollback_on_exception(self, repo, db):
        mock_session = MagicMock(spec=MeetingSession)
        db.flush.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.update(mock_session, {"status": SessionStatus.ENDED})
        db.rollback.assert_called()

    async def test_finish_session_success(self, repo, db):
        session_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        now = datetime.now(timezone.utc)
        mock_session = MagicMock(spec=MeetingSession)
        mock_session.started_at = now
        db.execute.side_effect = [
            _mock_execute_return(mock_session),
            _mock_execute_return(mock_session),
        ]
        result = await repo.finish_session(session_id)
        assert result is not None

    async def test_finish_session_returns_none_when_not_found(self, repo, db):
        db.execute.return_value = _mock_execute_return(None)
        result = await repo.finish_session(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert result is None

    async def test_count_participants_for_session(self, repo, db):
        session_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        db.execute.return_value = _mock_execute_return(5)
        result = await repo.count_participants_for_session(session_id)
        assert result == 5

    async def test_count_participants_returns_zero_when_none(self, repo, db):
        session_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        db.execute.return_value = _mock_execute_return(0)
        result = await repo.count_participants_for_session(session_id)
        assert result == 0

    async def test_get_participants_for_session(self, repo, db):
        session_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_p = MagicMock(spec=MeetingParticipant)
        db.execute.return_value = MagicMock()
        db.execute.return_value.all.return_value = [(mock_p, "Alice")]
        result = await repo.get_participants_for_session(session_id)
        assert len(result) == 1
        assert result[0] == mock_p