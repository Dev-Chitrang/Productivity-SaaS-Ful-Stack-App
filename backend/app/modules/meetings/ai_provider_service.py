import json
import time
from typing import Dict, Any

from openai import AsyncOpenAI, OpenAIError
from pydantic import ValidationError  # Clean specific catch for schema matching

from app.core.config import settings
from app.core.logger import logger
from app.modules.meetings.schemas import AIAnalysisPayloadSchema


class AIProviderService:
    """
    Decoupled interface handling remote LLM API communication pipelines.
    Configured to target NVIDIA NIM infrastructure wrappers natively.
    """

    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=settings.NVIDIA_NIM_API_KEY
        )

        self.model = "meta/llama-3.3-70b-instruct"

    async def generate_transcript_analysis(
        self,
        agenda: str,
        transcript_text: str,
    ) -> Dict[str, Any]:

        agenda = agenda or ""
        transcript_text = transcript_text or ""

        agenda_chars = len(agenda)
        transcript_chars = len(transcript_text)

        logger.info(
            "Meeting AI request started | model=%s | agenda_chars=%d | transcript_chars=%d",
            self.model,
            agenda_chars,
            transcript_chars,
        )

        system_prompt = """
You are an AI Meeting Assistant.

Analyze ONLY the provided meeting agenda and transcript.

Your responsibilities are:
1. Produce a concise executive summary.
2. Estimate agenda coverage as an integer percentage between 0 and 100.
3. List agenda items that were covered.
4. List discussion points that were outside the agenda.
5. Suggest actionable tasks that naturally emerged from the discussion.

Return ONLY valid JSON matching this schema:
{
  "summary": "Executive summary",
  "coverage_percentage": 0,
  "covered_points": ["Point 1"],
  "out_of_agenda_points": ["Point 1"],
  "suggested_tasks": [
    {
      "title": "Task title",
      "description": "Task description",
      "priority": "HIGH"
    }
  ]
}
"""

        user_content = (
            f"Agenda:\n{agenda}\n\n"
            f"Transcript:\n{transcript_text}"
        )

        start_time = time.monotonic()

        try:
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.2,
                top_p=0.7,
                max_tokens=2048,
                stream=False,
                response_format={"type": "json_object"},
            )

            elapsed = time.monotonic() - start_time

            logger.info(
                "Meeting AI completed successfully | model=%s | elapsed=%.2fs",
                self.model,
                elapsed,
            )

            content_string = completion.choices[0].message.content

            if not content_string:
                raise ValueError("NVIDIA NIM returned an empty response.")

            try:
                parsed_json = json.loads(content_string)
            except json.JSONDecodeError:
                logger.exception("Meeting AI returned invalid JSON structures.")
                raise

            try:
                AIAnalysisPayloadSchema.model_validate(parsed_json)
            except ValidationError: # <-- Explicitly catches model mismatch validation
                logger.exception(
                    "Meeting AI returned JSON that does not match AIAnalysisPayloadSchema."
                )
                raise

            return {
                "parsed": parsed_json,
                "raw": completion.model_dump(),
            }

        except OpenAIError:
            elapsed = time.monotonic() - start_time
            logger.exception(
                "Meeting AI provider error | model=%s | transcript_chars=%d | elapsed=%.2fs",
                self.model,
                transcript_chars,
                elapsed,
            )
            raise
