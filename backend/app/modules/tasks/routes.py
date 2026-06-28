from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, status, Query

from app.modules.tasks.dependencies import get_current_user_id, get_tasks_service
from app.modules.tasks.controller import TaskController
from app.modules.tasks.schemas import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse, TaskHistoryListResponse
from app.modules.tasks.enums import TaskStatus, TaskPriority

router = APIRouter(prefix="/tasks", tags=["Unified Tasks Management Engine"])

@router.post("", status_code=status.HTTP_201_CREATED, response_model=TaskResponse)
async def create_task_endpoint(
    payload: TaskCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_tasks_service)
):
    ctrl = TaskController(service)
    return await ctrl.create_user_task(current_user_id, payload)

@router.get("", status_code=status.HTTP_200_OK, response_model=TaskListResponse)
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
    sort_by: str = Query("updated_at", enum=["created_at", "updated_at", "due_date", "title", "priority"]),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_tasks_service)
):
    ctrl = TaskController(service)
    return await ctrl.list_user_tasks(
        current_user_id, search, status_filter, priority, label, favorite, pinned, archived, deleted, due_date, sort_by, sort_order
    )

@router.get("/{task_id}", status_code=status.HTTP_200_OK, response_model=TaskResponse)
async def get_task_endpoint(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_tasks_service)
):
    ctrl = TaskController(service)
    return await ctrl.get_user_task(current_user_id, task_id)

@router.patch("/{task_id}", status_code=status.HTTP_200_OK, response_model=TaskResponse)
async def update_task_endpoint(
    task_id: UUID,
    payload: TaskUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_tasks_service)
):
    ctrl = TaskController(service)
    return await ctrl.update_user_task(current_user_id, task_id, payload)

@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
async def delete_task_endpoint(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_tasks_service)
):
    ctrl = TaskController(service)
    return await ctrl.delete_user_task(current_user_id, task_id)

@router.patch("/{task_id}/restore", status_code=status.HTTP_200_OK, response_model=TaskResponse)
async def restore_task_endpoint(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_tasks_service)
):
    ctrl = TaskController(service)
    return await ctrl.restore_user_task(current_user_id, task_id)

@router.patch("/{task_id}/archive", status_code=status.HTTP_200_OK, response_model=TaskResponse)
async def archive_task_endpoint(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_tasks_service)
):
    ctrl = TaskController(service)
    return await ctrl.archive_user_task(current_user_id, task_id)

@router.patch("/{task_id}/unarchive", status_code=status.HTTP_200_OK, response_model=TaskResponse)
async def unarchive_task_endpoint(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_tasks_service)
):
    ctrl = TaskController(service)
    return await ctrl.unarchive_user_task(current_user_id, task_id)

@router.patch("/{task_id}/pin", status_code=status.HTTP_200_OK, response_model=TaskResponse)
async def pin_task_endpoint(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_tasks_service)
):
    ctrl = TaskController(service)
    return await ctrl.pin_user_task(current_user_id, task_id)

@router.patch("/{task_id}/unpin", status_code=status.HTTP_200_OK, response_model=TaskResponse)
async def unpin_task_endpoint(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_tasks_service)
):
    ctrl = TaskController(service)
    return await ctrl.unpin_user_task(current_user_id, task_id)

@router.patch("/{task_id}/favorite", status_code=status.HTTP_200_OK, response_model=TaskResponse)
async def favorite_task_endpoint(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_tasks_service)
):
    ctrl = TaskController(service)
    return await ctrl.favorite_user_task(current_user_id, task_id)

@router.patch("/{task_id}/unfavorite", status_code=status.HTTP_200_OK, response_model=TaskResponse)
async def unfavorite_task_endpoint(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_tasks_service)
):
    ctrl = TaskController(service)
    return await ctrl.unfavorite_user_task(current_user_id, task_id)

@router.get("/{task_id}/history", status_code=status.HTTP_200_OK, response_model=TaskHistoryListResponse)
async def get_task_history_endpoint(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_tasks_service)
):
    ctrl = TaskController(service)
    return await ctrl.get_task_history_timeline(current_user_id, task_id)
