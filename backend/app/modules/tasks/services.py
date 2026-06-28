from datetime import datetime, timezone
from typing import Optional, Sequence, List
from uuid import UUID
import json

from app.modules.tasks.repository import TaskRepository
from app.models.tasks import Task, TaskHistory
from app.modules.tasks.schemas import TaskCreate, TaskUpdate, ChecklistItem
from app.modules.tasks.enums import TaskStatus, TaskPriority
from app.modules.tasks.exceptions import (
    TaskNotFoundException,
    TaskAccessDeniedException,
    TaskValidationError
)
from app.utils.tiptap_converter import tiptap_doc_to_plain_text

class TaskService:
    def __init__(self, repo: TaskRepository):
        self.repo = repo

    async def get_task(self, user_id: UUID, task_id: UUID, include_deleted: bool = False) -> Task:
        task = await self.repo.get_by_id(task_id, include_deleted=include_deleted)
        if not task:
            raise TaskNotFoundException(task_id)
        if task.user_id != user_id:
            raise TaskAccessDeniedException(task_id, user_id)
        return task

    async def get_task_history(self, user_id: UUID, task_id: UUID) -> Sequence[dict]:
        """Validates ownership limits and returns audit rows sorted descending by timestamp."""
        await self.get_task(user_id, task_id, include_deleted=True)
        return await self.repo.get_history_by_task_id(task_id)

    async def create_task(self, user_id: UUID, payload: TaskCreate) -> Task:
        # Part 1: Relaxed validation. Prevent setting *new* dates into the past, but allow 'Today'
        if payload.due_date and payload.due_date.date() < datetime.now(timezone.utc).date():
            raise TaskValidationError("Cannot set a new task due date to a day in the past.")

        task_dict = payload.model_dump()
        task_dict["checklist"] = [item.model_dump() for item in payload.checklist]

        task = await self.repo.create(user_id, task_dict)

        # Log creation trace entry
        await self.repo.create_history_bulk([{
            "task_id": task.id, "user_id": user_id, "action": "CREATED",
            "field_name": None, "old_value": None, "new_value": task.title
        }])
        return task

    async def update_task(self, user_id: UUID, task_id: UUID, payload: TaskUpdate) -> Task:
        task = await self.get_task(user_id, task_id, include_deleted=False)
        update_dict = payload.model_dump(exclude_unset=True)

        # Part 1: Allow modifications to past-due tasks. Only block if the patch shifts due_date to a past day.
        if "due_date" in update_dict and update_dict["due_date"] is not None:
            if update_dict["due_date"].date() < datetime.now(timezone.utc).date():
                raise TaskValidationError("Requested due date cannot be set to a day in the past.")

        if "checklist" in update_dict and update_dict["checklist"] is not None:
            update_dict["checklist"] = [item.model_dump() for item in payload.checklist]

        # Calculate history audit logs before committing mutations to the DB
        history_entries = self._track_changes(user_id, task, update_dict)

        updated_task = await self.repo.update(task, update_dict)
        await self.repo.create_history_bulk(history_entries)
        return updated_task

    def _track_changes(self, user_id: UUID, original: Task, updates: dict) -> List[dict]:
        """Helper to generate detailed history entries based on applied updates."""
        history = []
        for field, new_val in updates.items():
            old_val = getattr(original, field, None)

            if field in ["labels", "checklist", "description"]:
                if json.dumps(old_val, sort_keys=True) == json.dumps(new_val, sort_keys=True):
                    continue
            else:
                if old_val == new_val:
                    continue

            if isinstance(new_val, dict) and new_val.get("type") == "doc":
                new_val = tiptap_doc_to_plain_text(new_val, max_length=0)
            if isinstance(old_val, dict) and old_val.get("type") == "doc":
                old_val = tiptap_doc_to_plain_text(old_val, max_length=0)

            history.append({
                "task_id": original.id,
                "user_id": user_id,
                "action": "UPDATED",
                "field_name": field,
                "old_value": str(old_val) if old_val is not None else None,
                "new_value": str(new_val) if new_val is not None else None
            })
        return history

    async def delete_task(self, user_id: UUID, task_id: UUID) -> None:
        task = await self.get_task(user_id, task_id, include_deleted=False)
        await self.repo.soft_delete(task)
        await self.repo.create_history_bulk([{
            "task_id": task.id, "user_id": user_id, "action": "DELETED", "field_name": None, "old_value": None, "new_value": None
        }])

    async def restore_task(self, user_id: UUID, task_id: UUID) -> Task:
        task = await self.get_task(user_id, task_id, include_deleted=True)
        if not task.deleted_at:
            raise TaskValidationError("Task node is already active.")
        restored = await self.repo.restore(task)
        await self.repo.create_history_bulk([{
            "task_id": task.id, "user_id": user_id, "action": "RESTORED", "field_name": None, "old_value": None, "new_value": None
        }])
        return restored

    async def toggle_archive_status(self, user_id: UUID, task_id: UUID, archive: bool) -> Task:
        task = await self.get_task(user_id, task_id, include_deleted=False)
        action_str = "ARCHIVED" if archive else "UNARCHIVED"
        res = await self.repo.update(task, {"is_archived": archive})
        await self.repo.create_history_bulk([{
            "task_id": task.id, "user_id": user_id, "action": action_str, "field_name": "is_archived", "old_value": str(not archive), "new_value": str(archive)
        }])
        return res

    async def toggle_pin_status(self, user_id: UUID, task_id: UUID, pin: bool) -> Task:
        task = await self.get_task(user_id, task_id, include_deleted=False)
        res = await self.repo.update(task, {"is_pinned": pin})
        await self.repo.create_history_bulk([{
            "task_id": task.id, "user_id": user_id, "action": "PINNED" if pin else "UNPINNED", "field_name": "is_pinned", "old_value": str(not pin), "new_value": str(pin)
        }])
        return res

    async def toggle_favorite_status(self, user_id: UUID, task_id: UUID, favorite: bool) -> Task:
        task = await self.get_task(user_id, task_id, include_deleted=False)
        res = await self.repo.update(task, {"is_favorite": favorite})
        await self.repo.create_history_bulk([{
            "task_id": task.id, "user_id": user_id, "action": "FAVORITED" if favorite else "UNFAVORITED", "field_name": "is_favorite", "old_value": str(not favorite), "new_value": str(favorite)
        }])
        return res

    async def list_and_filter_tasks(
        self,
        user_id: UUID,
        search: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        label: Optional[str] = None,
        favorite: Optional[bool] = None,
        pinned: Optional[bool] = None,
        archived: Optional[bool] = False,
        deleted: bool = False,
        due_date: Optional[datetime] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc"
    ) -> Sequence[Task]:
        """Applies query safety mappings and delegates to the repository layer."""
        valid_sort_targets = ["created_at", "updated_at", "due_date", "title", "priority"]
        if sort_by not in valid_sort_targets:
            sort_by = "updated_at"

        return await self.repo.list_and_filter(
            user_id=user_id, search=search, status=status, priority=priority,
            label=label, favorite=favorite, pinned=pinned, archived=archived,
            deleted=deleted, due_date=due_date, sort_by=sort_by, sort_order=sort_order
        )
