import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.ai_suggestions.services import AISuggestionService
from app.modules.ai_suggestions.enums import SuggestionStatus
from app.modules.ai_suggestions.exceptions import (
    AISuggestionNotFoundException,
    AISuggestionValidationError,
)
from app.modules.tasks.enums import TaskPriority
from app.models.meeting_suggested_task import MeetingSuggestedTask


def _uuid(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _make_repo():
    return AsyncMock(spec=AISuggestionRepository if False else object)


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


def _make_task_service():
    svc = AsyncMock()
    task = MagicMock()
    task.id = _uuid("11111111-1111-1111-1111-111111111111")
    svc.create_task.return_value = task
    return svc


class TestAISuggestionService:
    @pytest.fixture
    def repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, repo):
        return AISuggestionService(repo)

    # ---- get_suggestion -------------------------------------------------
    async def test_get_suggestion_found(self, service, repo):
        suggestion = _make_suggestion()
        repo.get_by_id.return_value = suggestion
        result = await service.get_suggestion(suggestion.id)
        assert result is suggestion
        repo.get_by_id.assert_awaited_once_with(suggestion.id)

    async def test_get_suggestion_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        sid = _uuid("99999999-9999-9999-9999-999999999999")
        with pytest.raises(AISuggestionNotFoundException) as exc:
            await service.get_suggestion(sid)
        assert exc.value.suggestion_id == sid

    # ---- create_task_from_suggestion ----------------------------------
    async def test_create_task_no_title_override(self, service, repo):
        suggestion = _make_suggestion(title="Original Title", priority="HIGH")
        repo.get_by_id.return_value = suggestion
        repo.update.return_value = suggestion
        task_service = _make_task_service()

        result = await service.create_task_from_suggestion(
            _uuid("87654321-4321-8765-4321-876543218765"),
            suggestion.id,
            task_service,
        )
        # Task created with suggestion's title
        created_task = task_service.create_task.call_args[0][1]
        assert created_task.title == "Original Title"
        assert created_task.priority == TaskPriority.HIGH
        # Repo updated to CREATED with task id
        update_data = repo.update.call_args[0][1]
        assert update_data["status"] == SuggestionStatus.CREATED
        assert update_data["created_task_id"] == task_service.create_task.return_value.id
        assert result is suggestion

    async def test_create_task_with_title_override(self, service, repo):
        suggestion = _make_suggestion(title="Original Title", priority="MEDIUM")
        repo.get_by_id.return_value = suggestion
        repo.update.return_value = suggestion
        task_service = _make_task_service()

        await service.create_task_from_suggestion(
            _uuid("87654321-4321-8765-4321-876543218765"),
            suggestion.id,
            task_service,
            title_override="Overridden",
        )
        created_task = task_service.create_task.call_args[0][1]
        assert created_task.title == "Overridden"
        assert created_task.priority == TaskPriority.MEDIUM

    async def test_create_task_priority_low(self, service, repo):
        suggestion = _make_suggestion(priority="LOW")
        repo.get_by_id.return_value = suggestion
        repo.update.return_value = suggestion
        task_service = _make_task_service()
        await service.create_task_from_suggestion(
            _uuid("87654321-4321-8765-4321-876543218765"), suggestion.id, task_service
        )
        assert task_service.create_task.call_args[0][1].priority == TaskPriority.LOW

    async def test_create_task_priority_unknown_falls_back_to_medium(self, service, repo):
        suggestion = _make_suggestion(priority="URGENT_UNKNOWN")
        repo.get_by_id.return_value = suggestion
        repo.update.return_value = suggestion
        task_service = _make_task_service()
        await service.create_task_from_suggestion(
            _uuid("87654321-4321-8765-4321-876543218765"), suggestion.id, task_service
        )
        assert task_service.create_task.call_args[0][1].priority == TaskPriority.MEDIUM

    async def test_create_task_description_empty_when_none(self, service, repo):
        suggestion = _make_suggestion(description=None, priority="MEDIUM")
        repo.get_by_id.return_value = suggestion
        repo.update.return_value = suggestion
        task_service = _make_task_service()
        await service.create_task_from_suggestion(
            _uuid("87654321-4321-8765-4321-876543218765"), suggestion.id, task_service
        )
        assert task_service.create_task.call_args[0][1].description == {"text": ""}

    async def test_create_task_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        sid = _uuid("99999999-9999-9999-9999-999999999999")
        with pytest.raises(AISuggestionNotFoundException):
            await service.create_task_from_suggestion(
                _uuid("87654321-4321-8765-4321-876543218765"), sid, _make_task_service()
            )

    async def test_create_task_already_created_raises(self, service, repo):
        suggestion = _make_suggestion(status=SuggestionStatus.CREATED)
        repo.get_by_id.return_value = suggestion
        task_service = _make_task_service()
        with pytest.raises(AISuggestionValidationError):
            await service.create_task_from_suggestion(
                _uuid("87654321-4321-8765-4321-876543218765"),
                suggestion.id,
                task_service,
            )
        task_service.create_task.assert_not_called()

    async def test_create_task_already_rejected_raises(self, service, repo):
        suggestion = _make_suggestion(status=SuggestionStatus.REJECTED)
        repo.get_by_id.return_value = suggestion
        task_service = _make_task_service()
        with pytest.raises(AISuggestionValidationError):
            await service.create_task_from_suggestion(
                _uuid("87654321-4321-8765-4321-876543218765"),
                suggestion.id,
                task_service,
            )
        task_service.create_task.assert_not_called()

    # ---- reject_suggestion ---------------------------------------------
    async def test_reject_suggestion_happy_path(self, service, repo):
        suggestion = _make_suggestion(status=SuggestionStatus.PENDING)
        repo.get_by_id.return_value = suggestion
        repo.update.return_value = suggestion
        result = await service.reject_suggestion(
            _uuid("87654321-4321-8765-4321-876543218765"), suggestion.id
        )
        update_data = repo.update.call_args[0][1]
        assert update_data["status"] == SuggestionStatus.REJECTED
        assert result is suggestion

    async def test_reject_suggestion_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        sid = _uuid("99999999-9999-9999-9999-999999999999")
        with pytest.raises(AISuggestionNotFoundException):
            await service.reject_suggestion(
                _uuid("87654321-4321-8765-4321-876543218765"), sid
            )

    async def test_reject_suggestion_already_created_raises(self, service, repo):
        suggestion = _make_suggestion(status=SuggestionStatus.CREATED)
        repo.get_by_id.return_value = suggestion
        with pytest.raises(AISuggestionValidationError):
            await service.reject_suggestion(
                _uuid("87654321-4321-8765-4321-876543218765"), suggestion.id
            )

    async def test_reject_suggestion_already_rejected_raises(self, service, repo):
        suggestion = _make_suggestion(status=SuggestionStatus.REJECTED)
        repo.get_by_id.return_value = suggestion
        with pytest.raises(AISuggestionValidationError):
            await service.reject_suggestion(
                _uuid("87654321-4321-8765-4321-876543218765"), suggestion.id
            )

    # ---- list_suggestions ----------------------------------------------
    async def test_list_suggestions(self, service, repo):
        s1 = _make_suggestion(title="A")
        s2 = _make_suggestion(title="B")
        repo.list_by_analysis_id.return_value = [s1, s2]
        analysis_id = _uuid("87654321-4321-8765-4321-876543218765")
        result = await service.list_suggestions(analysis_id)
        assert result == [s1, s2]
        repo.list_by_analysis_id.assert_awaited_once_with(analysis_id)
