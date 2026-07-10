import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.modules.ai_suggestions.controller import AISuggestionController
from app.modules.ai_suggestions.schemas import (
    SuggestionResponse,
    SuggestionListResponse,
    CreateTaskFromSuggestionPayload,
)
from app.modules.ai_suggestions.enums import SuggestionStatus
from app.modules.ai_suggestions.exceptions import (
    AISuggestionNotFoundException,
    AISuggestionValidationError,
)
from app.models.meeting_suggested_task import MeetingSuggestedTask


def _uuid(value: str) -> uuid.UUID:
    return uuid.UUID(value)


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


class TestAISuggestionController:
    @pytest.fixture
    def suggestion_service(self):
        return AsyncMock()

    @pytest.fixture
    def task_service(self):
        return AsyncMock(spec=object)

    @pytest.fixture
    def controller(self, suggestion_service, task_service):
        return AISuggestionController(suggestion_service, task_service)

    # ---- create_task_from_suggestion ----------------------------------
    async def test_create_task_success(self, controller, suggestion_service):
        suggestion = _make_suggestion()
        suggestion_service.create_task_from_suggestion.return_value = suggestion
        payload = CreateTaskFromSuggestionPayload(title="Override")
        result = await controller.create_task_from_suggestion(
            _uuid("87654321-4321-8765-4321-876543218765"),
            suggestion.id,
            payload,
        )
        assert isinstance(result, SuggestionResponse)
        assert result.id == suggestion.id
        controller.suggestion_service.create_task_from_suggestion.assert_awaited_once()
        # payload.title passed through to service
        assert controller.suggestion_service.create_task_from_suggestion.call_args.kwargs["title_override"] == "Override"

    async def test_create_task_not_found_raises_404(self, controller, suggestion_service):
        suggestion_service.create_task_from_suggestion.side_effect = AISuggestionNotFoundException(
            _uuid("99999999-9999-9999-9999-999999999999")
        )
        with pytest.raises(HTTPException) as exc:
            await controller.create_task_from_suggestion(
                _uuid("87654321-4321-8765-4321-876543218765"),
                _uuid("99999999-9999-9999-9999-999999999999"),
                CreateTaskFromSuggestionPayload(),
            )
        assert exc.value.status_code == 404
        assert "not found" in str(exc.value.detail)

    async def test_create_task_validation_error_raises_400(self, controller, suggestion_service):
        suggestion_service.create_task_from_suggestion.side_effect = AISuggestionValidationError(
            "already CREATED"
        )
        with pytest.raises(HTTPException) as exc:
            await controller.create_task_from_suggestion(
                _uuid("87654321-4321-8765-4321-876543218765"),
                _uuid("12345678-1234-5678-1234-567812345678"),
                CreateTaskFromSuggestionPayload(),
            )
        assert exc.value.status_code == 400
        assert "already CREATED" in str(exc.value.detail)

    # ---- reject_suggestion --------------------------------------------
    async def test_reject_success(self, controller, suggestion_service):
        suggestion = _make_suggestion(status=SuggestionStatus.REJECTED)
        suggestion_service.reject_suggestion.return_value = suggestion
        result = await controller.reject_suggestion(
            _uuid("87654321-4321-8765-4321-876543218765"),
            suggestion.id,
        )
        assert isinstance(result, SuggestionResponse)
        assert result.status == SuggestionStatus.REJECTED

    async def test_reject_not_found_raises_404(self, controller, suggestion_service):
        suggestion_service.reject_suggestion.side_effect = AISuggestionNotFoundException(
            _uuid("99999999-9999-9999-9999-999999999999")
        )
        with pytest.raises(HTTPException) as exc:
            await controller.reject_suggestion(
                _uuid("87654321-4321-8765-4321-876543218765"),
                _uuid("99999999-9999-9999-9999-999999999999"),
            )
        assert exc.value.status_code == 404

    async def test_reject_validation_error_raises_400(self, controller, suggestion_service):
        suggestion_service.reject_suggestion.side_effect = AISuggestionValidationError(
            "already REJECTED"
        )
        with pytest.raises(HTTPException) as exc:
            await controller.reject_suggestion(
                _uuid("87654321-4321-8765-4321-876543218765"),
                _uuid("12345678-1234-5678-1234-567812345678"),
            )
        assert exc.value.status_code == 400

    # ---- list_suggestions ---------------------------------------------
    async def test_list_suggestions(self, controller, suggestion_service):
        s1 = _make_suggestion(title="A")
        s2 = _make_suggestion(title="B")
        suggestion_service.list_suggestions.return_value = [s1, s2]
        result = await controller.list_suggestions(_uuid("87654321-4321-8765-4321-876543218765"))
        assert isinstance(result, SuggestionListResponse)
        assert result.total_count == 2
        assert len(result.suggestions) == 2

    async def test_list_suggestions_empty(self, controller, suggestion_service):
        suggestion_service.list_suggestions.return_value = []
        result = await controller.list_suggestions(_uuid("87654321-4321-8765-4321-876543218765"))
        assert result.total_count == 0
