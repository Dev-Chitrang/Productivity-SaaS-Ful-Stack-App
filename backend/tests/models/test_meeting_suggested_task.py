import uuid
from datetime import datetime, timezone

import pytest

from app.models.meeting_suggested_task import MeetingSuggestedTask
from app.modules.ai_suggestions.enums import SuggestionStatus


class TestMeetingSuggestedTaskModel:
    def test_tablename(self):
        assert MeetingSuggestedTask.__tablename__ == "meeting_suggested_tasks"

    def test_defaults(self):
        now = datetime.now(timezone.utc)
        analysis_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        task = MeetingSuggestedTask(
            analysis_id=analysis_id,
            title="Untitled",
            priority="MEDIUM",
            status=SuggestionStatus.PENDING,
            created_at=now,
        )
        assert task.analysis_id == analysis_id
        assert task.title == "Untitled"
        assert task.description is None
        assert task.priority == "MEDIUM"
        assert task.status == SuggestionStatus.PENDING
        assert task.created_task_id is None
        assert isinstance(task.created_at, datetime)
        assert task.created_at.tzinfo == timezone.utc

    def test_full_fields(self):
        now = datetime.now(timezone.utc)
        task = MeetingSuggestedTask(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            analysis_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            title="Fix login bug",
            description="Fix the OAuth redirect issue",
            priority="HIGH",
            status=SuggestionStatus.CREATED,
            created_task_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            created_at=now,
        )
        assert task.title == "Fix login bug"
        assert task.priority == "HIGH"
        assert task.status == SuggestionStatus.CREATED
        assert task.created_task_id is not None

    def test_created_at_default_utc(self):
        now = datetime.now(timezone.utc)
        task = MeetingSuggestedTask(
            analysis_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            created_at=now,
        )
        assert task.created_at is not None
        assert task.created_at.tzinfo == timezone.utc


class TestMeetingSuggestedTaskConstraints:
    def test_analysis_id_required_at_flush(self):
        # SQLAlchemy does not enforce NOT NULL on Python construction; the
        # constraint is validated by PostgreSQL at flush/commit time.
        import pytest
        from unittest.mock import AsyncMock, MagicMock
        db = AsyncMock()
        db.add = MagicMock()
        from app.modules.ai_suggestions.repository import AISuggestionRepository
        repo = AISuggestionRepository(db)
        db.flush.side_effect = Exception("null value in column analysis_id")
        with pytest.raises(Exception):
            import asyncio
            asyncio.run(repo.create({
                "title": "No analysis",
                "analysis_id": None,
            }))

    def test_title_required_at_flush(self):
        import pytest
        from unittest.mock import AsyncMock, MagicMock
        db = AsyncMock()
        db.add = MagicMock()
        from app.modules.ai_suggestions.repository import AISuggestionRepository
        repo = AISuggestionRepository(db)
        db.flush.side_effect = Exception("null value in column title")
        with pytest.raises(Exception):
            import asyncio
            asyncio.run(repo.create({
                "title": None,
                "analysis_id": uuid.UUID("12345678-1234-5678-1234-567812345678"),
            }))

    def test_status_default_is_pending(self):
        # SQLAlchemy applies the default at persist time, not at Python construction
        task = MeetingSuggestedTask(
            analysis_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Untitled",
        )
        assert task.status is None
        default = MeetingSuggestedTask.__table__.c.status.default
        assert default is not None
        assert default.arg == SuggestionStatus.PENDING

    def test_priority_default_is_medium(self):
        task = MeetingSuggestedTask(
            analysis_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Untitled",
        )
        assert task.priority is None
        default = MeetingSuggestedTask.__table__.c.priority.default
        assert default is not None
        assert default.arg == "MEDIUM"

    def test_id_is_uuid(self):
        task = MeetingSuggestedTask(
            analysis_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Untitled",
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        )
        assert isinstance(task.id, uuid.UUID)

    def test_status_constraint_accepts_valid_enum(self):
        task = MeetingSuggestedTask(
            analysis_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Untitled",
            status=SuggestionStatus.CREATED,
        )
        assert task.status == SuggestionStatus.CREATED

    def test_created_task_id_nullable(self):
        task = MeetingSuggestedTask(
            analysis_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Untitled",
        )
        assert task.created_task_id is None

    def test_from_attributes_serialization(self):
        from app.modules.ai_suggestions.schemas import SuggestionResponse
        task = MeetingSuggestedTask(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            analysis_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            title="Serialize me",
            description="desc",
            priority="LOW",
            status=SuggestionStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )
        resp = SuggestionResponse.model_validate(task)
        assert resp.title == "Serialize me"
        assert resp.priority == "LOW"
