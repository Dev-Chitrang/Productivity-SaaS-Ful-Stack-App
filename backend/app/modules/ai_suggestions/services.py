from typing import Optional, Sequence
from uuid import UUID

from app.modules.ai_suggestions.repository import AISuggestionRepository
from app.models.meeting_suggested_task import MeetingSuggestedTask
from app.modules.ai_suggestions.enums import SuggestionStatus
from app.modules.ai_suggestions.exceptions import (
    AISuggestionNotFoundException,
    AISuggestionAccessDeniedException,
    AISuggestionValidationError,
)


class AISuggestionService:
    def __init__(self, repo: AISuggestionRepository):
        self.repo = repo

    async def get_suggestion(self, suggestion_id: UUID) -> MeetingSuggestedTask:
        suggestion = await self.repo.get_by_id(suggestion_id)
        if not suggestion:
            raise AISuggestionNotFoundException(suggestion_id)
        return suggestion

    async def create_task_from_suggestion(
        self,
        user_id: UUID,
        suggestion_id: UUID,
        task_service,
        title_override: Optional[str] = None,
    ) -> MeetingSuggestedTask:
        suggestion = await self.get_suggestion(suggestion_id)

        if suggestion.status != SuggestionStatus.PENDING:
            raise AISuggestionValidationError(
                f"Suggestion is already '{suggestion.status.value}'. Only PENDING suggestions can be converted to tasks."
            )

        from app.modules.tasks.schemas import TaskCreate
        from app.modules.tasks.enums import TaskPriority

        priority_map = {
            "HIGH": TaskPriority.HIGH,
            "MEDIUM": TaskPriority.MEDIUM,
            "LOW": TaskPriority.LOW,
        }

        task_title = title_override or suggestion.title
        task_payload = TaskCreate(
            title=task_title,
            description={"text": suggestion.description or ""},
            priority=priority_map.get(suggestion.priority.upper(), TaskPriority.MEDIUM),
        )

        task = await task_service.create_task(user_id, task_payload)

        updated = await self.repo.update(
            suggestion,
            {
                "status": SuggestionStatus.CREATED,
                "created_task_id": task.id,
            },
        )

        return updated

    async def reject_suggestion(self, user_id: UUID, suggestion_id: UUID) -> MeetingSuggestedTask:
        suggestion = await self.get_suggestion(suggestion_id)

        if suggestion.status != SuggestionStatus.PENDING:
            raise AISuggestionValidationError(
                f"Suggestion is already '{suggestion.status.value}'. Only PENDING suggestions can be rejected."
            )

        return await self.repo.update(suggestion, {"status": SuggestionStatus.REJECTED})

    async def list_suggestions(self, analysis_id: UUID) -> Sequence[MeetingSuggestedTask]:
        return await self.repo.list_by_analysis_id(analysis_id)
