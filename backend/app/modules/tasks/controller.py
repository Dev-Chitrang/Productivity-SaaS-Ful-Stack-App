from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi import HTTPException, status

from app.modules.tasks.services import TaskService
from app.modules.tasks.schemas import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse, TaskHistoryListResponse, TaskHistoryResponse
from app.modules.tasks.enums import TaskStatus, TaskPriority
from app.modules.tasks.exceptions import (
    TaskNotFoundException,
    TaskAccessDeniedException,
    TaskValidationError
)

class TaskController:
    def __init__(self, service: TaskService):
        self.service = service

    async def create_user_task(self, user_id: UUID, payload: TaskCreate) -> dict:
        try:
            task = await self.service.create_task(user_id, payload)
            return TaskResponse.model_validate(task)
        except TaskValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_user_task(self, user_id: UUID, task_id: UUID) -> dict:
        try:
            task = await self.service.get_task(user_id, task_id, include_deleted=True)
            return TaskResponse.model_validate(task)
        except TaskNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except TaskAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def update_user_task(self, user_id: UUID, task_id: UUID, payload: TaskUpdate) -> dict:
        try:
            task = await self.service.update_task(user_id, task_id, payload)
            return TaskResponse.model_validate(task)
        except TaskNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except TaskAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except TaskValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def delete_user_task(self, user_id: UUID, task_id: UUID) -> dict:
        try:
            await self.service.delete_task(user_id, task_id)
            return {"status": "success", "message": "Task moved to trash successfully."}
        except TaskNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except TaskAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def restore_user_task(self, user_id: UUID, task_id: UUID) -> dict:
        try:
            task = await self.service.restore_task(user_id, task_id)
            return TaskResponse.model_validate(task)
        except TaskNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except TaskAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except TaskValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def archive_user_task(self, user_id: UUID, task_id: UUID) -> dict:
        try:
            task = await self.service.toggle_archive_status(user_id, task_id, archive=True)
            return TaskResponse.model_validate(task)
        except TaskNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except TaskAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def unarchive_user_task(self, user_id: UUID, task_id: UUID) -> dict:
        try:
            task = await self.service.toggle_archive_status(user_id, task_id, archive=False)
            return TaskResponse.model_validate(task)
        except TaskNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except TaskAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def pin_user_task(self, user_id: UUID, task_id: UUID) -> dict:
        try:
            task = await self.service.toggle_pin_status(user_id, task_id, pin=True)
            return TaskResponse.model_validate(task)
        except TaskNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except TaskAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def unpin_user_task(self, user_id: UUID, task_id: UUID) -> dict:
        try:
            task = await self.service.toggle_pin_status(user_id, task_id, pin=False)
            return TaskResponse.model_validate(task)
        except TaskNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except TaskAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def favorite_user_task(self, user_id: UUID, task_id: UUID) -> dict:
        try:
            task = await self.service.toggle_favorite_status(user_id, task_id, favorite=True)
            return TaskResponse.model_validate(task)
        except TaskNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except TaskAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def unfavorite_user_task(self, user_id: UUID, task_id: UUID) -> dict:
        try:
            task = await self.service.toggle_favorite_status(user_id, task_id, favorite=False)
            return TaskResponse.model_validate(task)
        except TaskNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except TaskAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def get_analytics(self, user_id: UUID) -> dict:
        return await self.service.get_analytics(user_id)

    async def list_user_tasks(
        self,
        user_id: UUID,
        search: Optional[str],
        status_filter: Optional[TaskStatus],
        priority: Optional[TaskPriority],
        label: Optional[str],
        favorite: Optional[bool],
        pinned: Optional[bool],
        archived: Optional[bool],
        deleted: bool,
        due_date: Optional[datetime],
        sort_by: str,
        sort_order: str
    ) -> dict:
        tasks = await self.service.list_and_filter_tasks(
            user_id=user_id, search=search, status=status_filter, priority=priority,
            label=label, favorite=favorite, pinned=pinned, archived=archived,
            deleted=deleted, due_date=due_date, sort_by=sort_by, sort_order=sort_order
        )
        return TaskListResponse(
            tasks=[TaskResponse.model_validate(t) for t in tasks],
            total_count=len(tasks)
        )

    async def get_task_history_timeline(self, user_id: UUID, task_id: UUID) -> dict:
        try:
            history = await self.service.get_task_history(user_id, task_id)
            return TaskHistoryListResponse(
                history=[TaskHistoryResponse.model_validate(h) for h in history],
                total_count=len(history)
            )
        except TaskNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except TaskAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
