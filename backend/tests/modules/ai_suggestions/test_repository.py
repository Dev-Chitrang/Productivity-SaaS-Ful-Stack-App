import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.ai_suggestions.repository import AISuggestionRepository
from app.modules.ai_suggestions.enums import SuggestionStatus
from app.models.meeting_suggested_task import MeetingSuggestedTask


def _uuid(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _make_db():
    db = AsyncMock()
    db.add = MagicMock()  # AsyncSession.add is a synchronous method
    return db


def _mock_execute_return(value):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = value
    mock_result.scalars.return_value.all.return_value = value if isinstance(value, list) else [value]
    mock_result.scalar.return_value = value if not isinstance(value, list) else len(value)
    mock_result.all.return_value = value if isinstance(value, list) else [value]
    return mock_result


def _make_suggestion(**overrides) -> MeetingSuggestedTask:
    defaults = dict(
        id=_uuid("12345678-1234-5678-1234-567812345678"),
        analysis_id=_uuid("87654321-4321-8765-4321-876543218765"),
        title="Fix login bug",
        description="OAuth redirect broken",
        priority="HIGH",
        status=SuggestionStatus.PENDING,
        created_task_id=None,
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return MeetingSuggestedTask(**defaults)


class TestAISuggestionRepository:
    @pytest.fixture
    def db(self):
        return _make_db()

    @pytest.fixture
    def repo(self, db):
        return AISuggestionRepository(db)

    # ---- create ---------------------------------------------------------
    async def test_create_happy_path(self, repo, db):
        data = {
            "analysis_id": _uuid("87654321-4321-8765-4321-876543218765"),
            "title": "New task",
            "description": "desc",
            "priority": "MEDIUM",
        }
        suggestion = await repo.create(data)
        assert isinstance(suggestion, MeetingSuggestedTask)
        assert suggestion.title == "New task"
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    async def test_create_rolls_back_on_error(self, repo, db):
        db.flush.side_effect = RuntimeError("db down")
        with pytest.raises(RuntimeError):
            await repo.create({"title": "x"})
        db.add.assert_called_once()
        db.rollback.assert_awaited_once()

    # ---- get_by_id ------------------------------------------------------
    async def test_get_by_id_found(self, repo, db):
        existing = _make_suggestion()
        db.execute.return_value = _mock_execute_return(existing)
        result = await repo.get_by_id(existing.id)
        assert result is existing
        db.execute.assert_awaited_once()

    async def test_get_by_id_not_found(self, repo, db):
        db.execute.return_value = _mock_execute_return(None)
        result = await repo.get_by_id(_uuid("99999999-9999-9999-9999-999999999999"))
        assert result is None

    # ---- update ---------------------------------------------------------
    async def test_update_happy_path(self, repo, db):
        suggestion = _make_suggestion(status=SuggestionStatus.PENDING)
        updated = await repo.update(
            suggestion, {"status": SuggestionStatus.CREATED, "created_task_id": _uuid("11111111-1111-1111-1111-111111111111")}
        )
        assert updated.status == SuggestionStatus.CREATED
        assert updated.created_task_id is not None
        db.add.assert_called_once_with(suggestion)
        db.flush.assert_awaited_once()

    async def test_update_rolls_back_on_error(self, repo, db):
        suggestion = _make_suggestion()
        db.flush.side_effect = RuntimeError("flush failed")
        with pytest.raises(RuntimeError):
            await repo.update(suggestion, {"status": SuggestionStatus.REJECTED})
        db.rollback.assert_awaited_once()

    # ---- list_by_analysis_id -------------------------------------------
    async def test_list_by_analysis_id(self, repo, db):
        s1 = _make_suggestion(title="A")
        s2 = _make_suggestion(title="B")
        db.execute.return_value = _mock_execute_return([s1, s2])
        result = await repo.list_by_analysis_id(_uuid("87654321-4321-8765-4321-876543218765"))
        assert isinstance(result, list)
        assert len(result) == 2

    async def test_list_by_analysis_id_empty(self, repo, db):
        db.execute.return_value = _mock_execute_return([])
        result = await repo.list_by_analysis_id(_uuid("87654321-4321-8765-4321-876543218765"))
        assert result == []

    # ---- bulk_create ----------------------------------------------------
    async def test_bulk_create_happy_path(self, repo, db):
        records = [
            {"analysis_id": _uuid("87654321-4321-8765-4321-876543218765"), "title": "T1", "priority": "LOW"},
            {"analysis_id": _uuid("87654321-4321-8765-4321-876543218765"), "title": "T2", "priority": "HIGH"},
        ]
        result = await repo.bulk_create(records)
        assert len(result) == 2
        assert all(isinstance(s, MeetingSuggestedTask) for s in result)
        assert db.add.call_count == 2
        db.flush.assert_awaited_once()

    async def test_bulk_create_empty(self, repo, db):
        result = await repo.bulk_create([])
        assert result == []
        db.add.assert_not_called()
        db.flush.assert_awaited_once()

    async def test_bulk_create_rolls_back_on_error(self, repo, db):
        db.flush.side_effect = RuntimeError("bulk fail")
        with pytest.raises(RuntimeError):
            await repo.bulk_create([{"title": "x"}])
        db.rollback.assert_awaited_once()
