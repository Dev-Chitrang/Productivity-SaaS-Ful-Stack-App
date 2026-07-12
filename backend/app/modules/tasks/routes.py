from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.modules.attachments.enums import AttachmentEntityType
from app.modules.attachments.exceptions import (
    AttachmentNotFoundException,
    AttachmentStorageError,
    AttachmentValidationError,
)
from app.modules.attachments.schemas import AttachmentListResponse, AttachmentResponse
from app.modules.attachments.service import AttachmentService
from app.modules.tasks.controller import TaskController
from app.modules.tasks.dependencies import (
    get_attachment_service,
    get_current_user_id,
    get_tasks_service,
)
from app.modules.tasks.enums import TaskPriority, TaskStatus
from app.modules.tasks.exceptions import TaskAccessDeniedException, TaskNotFoundException
from app.modules.tasks.schemas import (
    TaskCreate,
    TaskHistoryListResponse,
    TaskListResponse,
    TaskResponse,
    TaskUpdate,
)
from app.modules.tasks.services import TaskService

from app.core.rate_limit import RateLimiter

router = APIRouter(prefix="/tasks", tags=["Unified Tasks Management Engine"])


# ── Core Task CRUD ────────────────────────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED, response_model=TaskResponse, dependencies=[Depends(RateLimiter(20, 60, "write_entity"))])
async def create_task_endpoint(
    payload: TaskCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    service: TaskService = Depends(get_tasks_service),
):
    ctrl = TaskController(service)
    return await ctrl.create_user_task(current_user_id, payload)


@router.get("", status_code=status.HTTP_200_OK, response_model=TaskListResponse, dependencies=[Depends(RateLimiter(60, 60, "general_get"))])
async def list_tasks_endpoint(
    search: Optional[str] = None,
    status_filter: Optional[TaskStatus] = Query(None, alias="status"),
    priority: Optional[TaskPriority] = None,
    label: Optional[str] = None,
    favorite: Optional[bool] = None,
    pinned: Optional[bool] = None,
    archived: Optional[bool] = False,
    deleted: bool = False,
    due_date: Optional[datetime] = None,
    sort_by: str = Query(
        "updated_at",
        enum=["created_at", "updated_at", "due_date", "title", "priority"],
    ),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    current_user_id: UUID = Depends(get_current_user_id),
    service: TaskService = Depends(get_tasks_service),
):
    ctrl = TaskController(service)
    return await ctrl.list_user_tasks(
        current_user_id,
        search,
        status_filter,
        priority,
        label,
        favorite,
        pinned,
        archived,
        deleted,
        due_date,
        sort_by,
        sort_order,
    )


@router.get("/analytics", status_code=status.HTTP_200_OK, dependencies=[Depends(RateLimiter(60, 60, "general_get"))])
async def tasks_analytics_endpoint(
    current_user_id: UUID = Depends(get_current_user_id),
    service: TaskService = Depends(get_tasks_service),
):
    ctrl = TaskController(service)
    return await ctrl.get_analytics(current_user_id)


@router.get("/{task_id}", status_code=status.HTTP_200_OK, response_model=TaskResponse, dependencies=[Depends(RateLimiter(60, 60, "general_get"))])
async def get_task_endpoint(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: TaskService = Depends(get_tasks_service),
):
    ctrl = TaskController(service)
    return await ctrl.get_user_task(current_user_id, task_id)


@router.patch("/{task_id}", status_code=status.HTTP_200_OK, response_model=TaskResponse, dependencies=[Depends(RateLimiter(20, 60, "write_entity"))])
async def update_task_endpoint(
    task_id: UUID,
    payload: TaskUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    service: TaskService = Depends(get_tasks_service),
):
    ctrl = TaskController(service)
    return await ctrl.update_user_task(current_user_id, task_id, payload)


@router.delete("/{task_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(RateLimiter(20, 60, "write_entity"))])
async def delete_task_endpoint(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: TaskService = Depends(get_tasks_service),
):
    ctrl = TaskController(service)
    return await ctrl.delete_user_task(current_user_id, task_id)


@router.patch("/{task_id}/restore", status_code=status.HTTP_200_OK, response_model=TaskResponse, dependencies=[Depends(RateLimiter(20, 60, "write_entity"))])
async def restore_task_endpoint(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: TaskService = Depends(get_tasks_service),
):
    ctrl = TaskController(service)
    return await ctrl.restore_user_task(current_user_id, task_id)


@router.patch("/{task_id}/archive", status_code=status.HTTP_200_OK, response_model=TaskResponse, dependencies=[Depends(RateLimiter(20, 60, "write_entity"))])
async def archive_task_endpoint(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: TaskService = Depends(get_tasks_service),
):
    ctrl = TaskController(service)
    return await ctrl.archive_user_task(current_user_id, task_id)


@router.patch("/{task_id}/unarchive", status_code=status.HTTP_200_OK, response_model=TaskResponse, dependencies=[Depends(RateLimiter(20, 60, "write_entity"))])
async def unarchive_task_endpoint(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: TaskService = Depends(get_tasks_service),
):
    ctrl = TaskController(service)
    return await ctrl.unarchive_user_task(current_user_id, task_id)


@router.patch("/{task_id}/pin", status_code=status.HTTP_200_OK, response_model=TaskResponse, dependencies=[Depends(RateLimiter(20, 60, "write_entity"))])
async def pin_task_endpoint(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: TaskService = Depends(get_tasks_service),
):
    ctrl = TaskController(service)
    return await ctrl.pin_user_task(current_user_id, task_id)


@router.patch("/{task_id}/unpin", status_code=status.HTTP_200_OK, response_model=TaskResponse, dependencies=[Depends(RateLimiter(20, 60, "write_entity"))])
async def unpin_task_endpoint(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: TaskService = Depends(get_tasks_service),
):
    ctrl = TaskController(service)
    return await ctrl.unpin_user_task(current_user_id, task_id)


@router.patch("/{task_id}/favorite", status_code=status.HTTP_200_OK, response_model=TaskResponse, dependencies=[Depends(RateLimiter(20, 60, "write_entity"))])
async def favorite_task_endpoint(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: TaskService = Depends(get_tasks_service),
):
    ctrl = TaskController(service)
    return await ctrl.favorite_user_task(current_user_id, task_id)


@router.patch("/{task_id}/unfavorite", status_code=status.HTTP_200_OK, response_model=TaskResponse, dependencies=[Depends(RateLimiter(20, 60, "write_entity"))])
async def unfavorite_task_endpoint(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: TaskService = Depends(get_tasks_service),
):
    ctrl = TaskController(service)
    return await ctrl.unfavorite_user_task(current_user_id, task_id)


@router.get(
    "/{task_id}/history",
    status_code=status.HTTP_200_OK,
    response_model=TaskHistoryListResponse,
    dependencies=[Depends(RateLimiter(60, 60, "general_get"))],
)
async def get_task_history_endpoint(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: TaskService = Depends(get_tasks_service),
):
    ctrl = TaskController(service)
    return await ctrl.get_task_history_timeline(current_user_id, task_id)


# ── Task Attachments ──────────────────────────────────────────────────────────

async def _verify_task_access(
    task_id: UUID,
    current_user_id: UUID,
    task_service: TaskService,
) -> None:
    """Raise 404/403 if the task does not exist or the user does not own it."""
    try:
        await task_service.get_task(current_user_id, task_id, include_deleted=False)
    except TaskNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found.")
    except TaskAccessDeniedException:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this task.")


@router.post(
    "/{task_id}/attachments",
    status_code=status.HTTP_201_CREATED,
    response_model=AttachmentResponse,
    summary="Upload an attachment to a task",
    dependencies=[Depends(RateLimiter(3, 60, "file_upload"))],
)
async def upload_task_attachment(
    task_id: UUID,
    file: UploadFile = File(...),
    current_user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_tasks_service),
    attachment_service: AttachmentService = Depends(get_attachment_service),
):
    await _verify_task_access(task_id, current_user_id, task_service)
    try:
        attachment = await attachment_service.upload(
            owner_user_id=current_user_id,
            entity_type=AttachmentEntityType.TASK,
            entity_id=task_id,
            file=file,
        )
        return AttachmentResponse.model_validate(attachment)
    except AttachmentValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except AttachmentStorageError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get(
    "/{task_id}/attachments",
    status_code=status.HTTP_200_OK,
    response_model=AttachmentListResponse,
    summary="List all attachments for a task",
    dependencies=[Depends(RateLimiter(60, 60, "general_get"))],
)
async def list_task_attachments(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_tasks_service),
    attachment_service: AttachmentService = Depends(get_attachment_service),
):
    await _verify_task_access(task_id, current_user_id, task_service)
    attachments = await attachment_service.list_all_for_entity(
        AttachmentEntityType.TASK, task_id
    )
    return AttachmentListResponse(
        attachments=[AttachmentResponse.model_validate(a) for a in attachments],
        total_count=len(attachments),
    )


@router.get(
    "/{task_id}/attachments/{attachment_id}/download",
    response_class=FileResponse,
    summary="Download a task attachment",
    dependencies=[Depends(RateLimiter(60, 60, "general_get"))],
)
async def download_task_attachment(
    task_id: UUID,
    attachment_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_tasks_service),
    attachment_service: AttachmentService = Depends(get_attachment_service),
):
    await _verify_task_access(task_id, current_user_id, task_service)
    try:
        attachment = await attachment_service.get_for_download_verified(
            attachment_id, AttachmentEntityType.TASK, task_id
        )
        return FileResponse(
            path=attachment.storage_path,
            media_type=attachment.content_type,
            filename=attachment.original_filename,
        )
    except AttachmentNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")


@router.delete(
    "/{task_id}/attachments/{attachment_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a task attachment",
    dependencies=[Depends(RateLimiter(20, 60, "write_entity"))],
)
async def delete_task_attachment(
    task_id: UUID,
    attachment_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_tasks_service),
    attachment_service: AttachmentService = Depends(get_attachment_service),
):
    await _verify_task_access(task_id, current_user_id, task_service)
    try:
        await attachment_service.delete_verified(
            attachment_id, AttachmentEntityType.TASK, task_id
        )
        return {"status": "success", "message": "Attachment deleted successfully."}
    except AttachmentNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")
