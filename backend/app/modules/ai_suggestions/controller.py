from typing import Optional, List
from uuid import UUID
from fastapi import HTTPException, status

from app.modules.ai_suggestions.services import AISuggestionService
from app.modules.ai_suggestions.schemas import (
    SuggestionResponse,
    SuggestionListResponse,
    CreateTaskFromSuggestionPayload,
)
from app.modules.ai_suggestions.exceptions import (
    AISuggestionNotFoundException,
    AISuggestionValidationError,
)
from app.modules.tasks.services import TaskService


class AISuggestionController:
    def __init__(self, suggestion_service: AISuggestionService, task_service: TaskService):
        self.suggestion_service = suggestion_service
        self.task_service = task_service

    async def create_task_from_suggestion(
        self,
        user_id: UUID,
        suggestion_id: UUID,
        payload: CreateTaskFromSuggestionPayload,
    ) -> dict:
        try:
            suggestion = await self.suggestion_service.create_task_from_suggestion(
                user_id,
                suggestion_id,
                self.task_service,
                title_override=payload.title,
            )
            return SuggestionResponse.model_validate(suggestion)
        except AISuggestionNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except AISuggestionValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def reject_suggestion(self, user_id: UUID, suggestion_id: UUID) -> dict:
        try:
            suggestion = await self.suggestion_service.reject_suggestion(user_id, suggestion_id)
            return SuggestionResponse.model_validate(suggestion)
        except AISuggestionNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except AISuggestionValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def list_suggestions(self, analysis_id: UUID) -> dict:
        suggestions = await self.suggestion_service.list_suggestions(analysis_id)
        return SuggestionListResponse(
            suggestions=[SuggestionResponse.model_validate(s) for s in suggestions],
            total_count=len(suggestions),
        )
