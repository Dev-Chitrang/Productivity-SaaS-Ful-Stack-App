import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.meetings.ai_provider_service import AIProviderService
from app.modules.meetings.schemas import AIAnalysisPayloadSchema


class TestAIProviderService:
    @pytest.fixture
    def provider(self):
        with patch("app.modules.meetings.ai_provider_service.settings") as mock_settings:
            mock_settings.NVIDIA_NIM_API_KEY = "test_key"
            p = AIProviderService()
            p.client = AsyncMock()
            return p

    async def test_model_name(self, provider):
        assert provider.model == "meta/llama-3.3-70b-instruct"

    async def test_generate_transcript_analysis_success(self, provider):
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = '{"summary": "Summary", "coverage_percentage": 85, "covered_points": [], "out_of_agenda_points": [], "suggested_tasks": []}'
        provider.client.chat.completions.create.return_value = mock_completion

        result = await provider.generate_transcript_analysis("Agenda", "Transcript text")
        assert "parsed" in result
        assert result["parsed"]["summary"] == "Summary"

    async def test_generate_transcript_analysis_uses_json_mode(self, provider):
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = '{"summary": "Summary", "coverage_percentage": 50, "covered_points": [], "out_of_agenda_points": [], "suggested_tasks": []}'
        provider.client.chat.completions.create.return_value = mock_completion

        await provider.generate_transcript_analysis("Agenda", "Transcript")
        provider.client.chat.completions.create.assert_called_once()
        call_kwargs = provider.client.chat.completions.create.call_args[1]
        assert call_kwargs["response_format"] == {"type": "json_object"}

    async def test_generate_transcript_analysis_empty_response_raises(self, provider):
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = ""
        provider.client.chat.completions.create.return_value = mock_completion

        with pytest.raises(ValueError, match="empty response"):
            await provider.generate_transcript_analysis("Agenda", "Transcript")

    async def test_generate_transcript_analysis_invalid_json_raises(self, provider):
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = "not json"
        provider.client.chat.completions.create.return_value = mock_completion

        with pytest.raises(Exception):
            await provider.generate_transcript_analysis("Agenda", "Transcript")

    async def test_generate_transcript_analysis_schema_mismatch_raises(self, provider):
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = '{"wrong_schema": true}'
        provider.client.chat.completions.create.return_value = mock_completion

        with pytest.raises(Exception):
            await provider.generate_transcript_analysis("Agenda", "Transcript")

    async def test_generate_transcript_analysis_empty_inputs(self, provider):
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = '{"summary": "", "coverage_percentage": 0, "covered_points": [], "out_of_agenda_points": [], "suggested_tasks": []}'
        provider.client.chat.completions.create.return_value = mock_completion

        result = await provider.generate_transcript_analysis("", "")
        assert result["parsed"]["summary"] == ""

    async def test_generate_transcript_analysis_logs_start_and_end(self, provider):
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = '{"summary": "s", "coverage_percentage": 0, "covered_points": [], "out_of_agenda_points": [], "suggested_tasks": []}'
        provider.client.chat.completions.create.return_value = mock_completion

        with patch("app.modules.meetings.ai_provider_service.logger") as mock_logger:
            await provider.generate_transcript_analysis("agenda", "transcript")
            assert any("Meeting AI request started" in str(c) for c in mock_logger.info.call_args_list)
            assert any("Meeting AI completed successfully" in str(c) for c in mock_logger.info.call_args_list)
