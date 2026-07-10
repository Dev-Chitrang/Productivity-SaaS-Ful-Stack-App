import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.modules.ai_suggestions.schemas import (
    SuggestionResponse,
    SuggestionListResponse,
    CreateTaskFromSuggestionPayload,
)
from app.modules.ai_suggestions.enums import SuggestionStatus
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


class TestSuggestionResponse:
    def test_valid_from_attributes(self):
        suggestion = _make_suggestion()
        resp = SuggestionResponse.model_validate(suggestion)
        assert resp.id == suggestion.id
        assert resp.analysis_id == suggestion.analysis_id
        assert resp.title == "Fix login bug"
        assert resp.description == "OAuth redirect broken"
        assert resp.priority == "HIGH"
        assert resp.status == SuggestionStatus.PENDING
        assert resp.created_task_id is None
        assert isinstance(resp.created_at, datetime)

    def test_valid_with_created_status_and_task(self):
        tid = _uuid("11111111-1111-1111-1111-111111111111")
        suggestion = _make_suggestion(
            status=SuggestionStatus.CREATED, created_task_id=tid
        )
        resp = SuggestionResponse.model_validate(suggestion)
        assert resp.status == SuggestionStatus.CREATED
        assert resp.created_task_id == tid

    def test_from_dict(self):
        resp = SuggestionResponse(
            id=_uuid("12345678-1234-5678-1234-567812345678"),
            analysis_id=_uuid("87654321-4321-8765-4321-876543218765"),
            title="Title",
            description=None,
            priority="LOW",
            status=SuggestionStatus.REJECTED,
            created_task_id=None,
            created_at=datetime.now(timezone.utc),
        )
        assert resp.title == "Title"
        assert resp.priority == "LOW"

    def test_optional_fields_accept_none(self):
        resp = SuggestionResponse(
            id=_uuid("12345678-1234-5678-1234-567812345678"),
            analysis_id=_uuid("87654321-4321-8765-4321-876543218765"),
            title="Title",
            priority="MEDIUM",
            status=SuggestionStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )
        assert resp.description is None

    def test_invalid_status_rejected(self):
        with pytest.raises(ValidationError):
            SuggestionResponse(
                id=_uuid("12345678-1234-5678-1234-567812345678"),
                analysis_id=_uuid("87654321-4321-8765-4321-876543218765"),
                title="Title",
                priority="MEDIUM",
                status="BOGUS",
                created_at=datetime.now(timezone.utc),
            )


class TestSuggestionListResponse:
    def test_empty_list(self):
        resp = SuggestionListResponse(suggestions=[], total_count=0)
        assert resp.suggestions == []
        assert resp.total_count == 0

    def test_with_suggestions(self):
        s1 = _make_suggestion(title="A")
        s2 = _make_suggestion(title="B")
        resp = SuggestionListResponse(
            suggestions=[SuggestionResponse.model_validate(s1), SuggestionResponse.model_validate(s2)],
            total_count=2,
        )
        assert len(resp.suggestions) == 2
        assert resp.total_count == 2


class TestCreateTaskFromSuggestionPayload:
    def test_default_title_none(self):
        payload = CreateTaskFromSuggestionPayload()
        assert payload.title is None

    def test_with_title(self):
        payload = CreateTaskFromSuggestionPayload(title="Override")
        assert payload.title == "Override"

    def test_title_blank_is_allowed(self):
        # The payload itself does not forbid blank; validation occurs downstream
        payload = CreateTaskFromSuggestionPayload(title="")
        assert payload.title == ""

    def test_serialization_roundtrip(self):
        payload = CreateTaskFromSuggestionPayload(title="Custom")
        dumped = payload.model_dump()
        assert dumped["title"] == "Custom"
        rebuilt = CreateTaskFromSuggestionPayload(**dumped)
        assert rebuilt.title == "Custom"
