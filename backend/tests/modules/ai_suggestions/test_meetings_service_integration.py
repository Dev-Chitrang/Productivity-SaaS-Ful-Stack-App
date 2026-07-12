import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.meetings.service import MeetingAIAnalysisService


def _uuid(value: str) -> uuid.UUID:
    return uuid.UUID(value)


ANALYSIS_ID = _uuid("87654321-4321-8765-4321-876543218765")
SESSION_ID = _uuid("12345678-1234-5678-1234-567812345678")


class FakeAISuggestionRepository:
    def __init__(self, db):
        self.db = db

    bulk_create = AsyncMock(return_value=[])


def _make_repo():
    repo = AsyncMock()
    analysis = MagicMock()
    analysis.id = ANALYSIS_ID
    analysis.status = "PENDING"
    repo.get_by_session_id.return_value = analysis
    repo.create_analysis_placeholder.return_value = analysis
    return repo


def _make_provider(suggested_tasks=None):
    provider = AsyncMock()
    provider.generate_transcript_analysis.return_value = {
        "parsed": {
            "summary": "Summary",
            "coverage_percentage": 80,
            "covered_points": ["a"],
            "out_of_agenda_points": ["b"],
            "suggested_tasks": suggested_tasks if suggested_tasks is not None else [],
        },
        "raw": "raw text",
    }
    return provider


class TestMeetingAIAnalysisSuggestionIntegration:
    async def test_bulk_create_called_with_normalized_records(self):
        FakeAISuggestionRepository.bulk_create.reset_mock()
        repo = _make_repo()
        provider = _make_provider(
            suggested_tasks=[
                {"title": "Task A", "description": "desc A", "priority": "HIGH"},
                {"title": "Task B", "description": "", "priority": "LOW"},
                {},
            ]
        )
        service = MeetingAIAnalysisService(repo, provider)

        with patch(
            "app.modules.ai_suggestions.repository.AISuggestionRepository",
            FakeAISuggestionRepository,
        ):
            await service.process_async_transcript_analysis(
                SESSION_ID, "agenda", "transcript text"
            )

        # repository was constructed (inside the `if suggested_tasks:` block)
        # and bulk_create invoked once with 3 normalized records
        FakeAISuggestionRepository.bulk_create.assert_called_once()
        records = FakeAISuggestionRepository.bulk_create.call_args[0][0]
        assert len(records) == 3
        assert records[0]["analysis_id"] == ANALYSIS_ID
        assert records[0]["title"] == "Task A"
        assert records[0]["description"] == "desc A"
        assert records[0]["priority"] == "HIGH"
        # Missing fields fall back to defaults
        assert records[2]["title"] == "Untitled"
        assert records[2]["description"] == ""
        assert records[2]["priority"] == "MEDIUM"

    async def test_no_suggested_tasks_skips_bulk_create(self):
        FakeAISuggestionRepository.bulk_create.reset_mock()
        repo = _make_repo()
        provider = _make_provider(suggested_tasks=[])
        service = MeetingAIAnalysisService(repo, provider)

        with patch(
            "app.modules.ai_suggestions.repository.AISuggestionRepository",
            FakeAISuggestionRepository,
        ):
            await service.process_async_transcript_analysis(SESSION_ID, "agenda", "text")

        # No suggestions -> repository never constructed, bulk_create never invoked
        assert FakeAISuggestionRepository.bulk_create.call_args is None

    async def test_provider_error_marks_analysis_failed_and_reraises(self):
        repo = _make_repo()
        provider = AsyncMock()
        provider.generate_transcript_analysis.side_effect = RuntimeError("provider down")
        service = MeetingAIAnalysisService(repo, provider)

        with patch("app.modules.ai_suggestions.repository.AISuggestionRepository", FakeAISuggestionRepository):
            with pytest.raises(RuntimeError):
                await service.process_async_transcript_analysis(SESSION_ID, "agenda", "text")

        # update_status(analysis.id, FAILED, raw_response={...}) -> status is 2nd positional arg
        call_args = repo.update_status.call_args
        assert str(call_args.args[1]).endswith("FAILED")
        assert "error_log_payload" in call_args.kwargs["raw_response"]
