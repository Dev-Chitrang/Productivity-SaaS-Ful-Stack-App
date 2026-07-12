from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.modules.ai_suggestions.controller import AISuggestionController
from app.modules.ai_suggestions.dependencies import (
    get_current_user_id,
    get_ai_suggestion_service,
)
from app.modules.ai_suggestions.schemas import (
    SuggestionListResponse,
    SuggestionResponse,
    CreateTaskFromSuggestionPayload,
)
from app.modules.ai_suggestions.services import AISuggestionService
from app.modules.tasks.dependencies import get_tasks_service
from app.modules.tasks.services import TaskService

from app.core.rate_limit import RateLimiter

router = APIRouter(prefix="/ai-suggestions", tags=["AI Suggested Tasks"])


@router.post(
    "/{suggestion_id}/create-task",
    status_code=status.HTTP_200_OK,
    response_model=SuggestionResponse,
    dependencies=[Depends(RateLimiter(3, 60, "ai_analysis"))],
)
async def create_task_from_suggestion_endpoint(
    suggestion_id: UUID,
    payload: CreateTaskFromSuggestionPayload,
    current_user_id: UUID = Depends(get_current_user_id),
    suggestion_service: AISuggestionService = Depends(get_ai_suggestion_service),
    task_service: TaskService = Depends(get_tasks_service),
):
    ctrl = AISuggestionController(suggestion_service, task_service)
    return await ctrl.create_task_from_suggestion(current_user_id, suggestion_id, payload)


@router.post(
    "/{suggestion_id}/reject",
    status_code=status.HTTP_200_OK,
    response_model=SuggestionResponse,
    dependencies=[Depends(RateLimiter(3, 60, "ai_analysis"))],
)
async def reject_suggestion_endpoint(
    suggestion_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    suggestion_service: AISuggestionService = Depends(get_ai_suggestion_service),
    task_service: TaskService = Depends(get_tasks_service),
):
    ctrl = AISuggestionController(suggestion_service, task_service)
    return await ctrl.reject_suggestion(current_user_id, suggestion_id)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=SuggestionListResponse,
    dependencies=[Depends(RateLimiter(3, 60, "ai_analysis"))],
)
async def list_suggestions_endpoint(
    analysis_id: UUID = Query(..., description="Filter by AI analysis ID"),
    current_user_id: UUID = Depends(get_current_user_id),
    suggestion_service: AISuggestionService = Depends(get_ai_suggestion_service),
    task_service: TaskService = Depends(get_tasks_service),
):
    ctrl = AISuggestionController(suggestion_service, task_service)
    return await ctrl.list_suggestions(analysis_id)
