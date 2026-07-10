import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
import pytest
from fastapi import HTTPException, status
from app.modules.tasks.services import TaskService
from app.modules.tasks.controller import TaskController
from app.modules.tasks.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskHistoryListResponse,
    TaskHistoryResponse,
    UserInfo,
)
from app.modules.tasks.enums import TaskStatus, TaskPriority
from app.modules.tasks.exceptions import (
    TaskNotFoundException,
    TaskAccessDeniedException,
    TaskValidationError,
)


class TestTaskController:
    @pytest.fixture
    def controller(self):
        service = MagicMock(spec=TaskService)
        return TaskController(service)

    def _make_task_response(self, **kwargs):
        now = datetime.now(timezone.utc)
        return TaskResponse(
            id=kwargs.get("id", uuid.UUID("12345678-1234-5678-1234-567812345678")),
            user_id=kwargs.get("user_id", uuid.UUID("87654321-4321-8765-4321-876543218765")),
            title=kwargs.get("title", "Test Task"),
            description=kwargs.get("description", None),
            status=kwargs.get("status", TaskStatus.TODO),
            priority=kwargs.get("priority", TaskPriority.MEDIUM),
            due_date=kwargs.get("due_date", None),
            labels=kwargs.get("labels", []),
            checklist=kwargs.get("checklist", []),
            is_pinned=kwargs.get("is_pinned", False),
            is_favorite=kwargs.get("is_favorite", False),
            is_archived=kwargs.get("is_archived", False),
            created_at=now,
            updated_at=now,
            deleted_at=kwargs.get("deleted_at", None),
        )

    async def test_create_user_task_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        mock_task = self._make_task_response()
        controller.service.create_task.return_value = mock_task

        payload = TaskCreate(title="New Task", description=None)
        result = await controller.create_user_task(user_id, payload)
        assert result.title == "Test Task"
        controller.service.create_task.assert_called_once_with(user_id, payload)

    async def test_create_user_task_validation_error(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        controller.service.create_task.side_effect = TaskValidationError("past due date")
        payload = TaskCreate(title="Past Task", description=None)
        with pytest.raises(HTTPException) as exc_info:
            await controller.create_user_task(user_id, payload)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_get_user_task_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_task = self._make_task_response()
        controller.service.get_task.return_value = mock_task

        result = await controller.get_user_task(user_id, task_id)
        assert result.id == task_id
        controller.service.get_task.assert_called_once_with(user_id, task_id, include_deleted=True)

    async def test_get_user_task_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.get_task.side_effect = TaskNotFoundException(task_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.get_user_task(user_id, task_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_user_task_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.get_task.side_effect = TaskAccessDeniedException(task_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.get_user_task(user_id, task_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_update_user_task_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_task = self._make_task_response(title="Updated")
        controller.service.update_task.return_value = mock_task

        payload = TaskUpdate(title="Updated")
        result = await controller.update_user_task(user_id, task_id, payload)
        assert result.title == "Updated"
        controller.service.update_task.assert_called_once_with(user_id, task_id, payload)

    async def test_update_user_task_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.update_task.side_effect = TaskNotFoundException(task_id)
        payload = TaskUpdate(title="Updated")
        with pytest.raises(HTTPException) as exc_info:
            await controller.update_user_task(user_id, task_id, payload)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_user_task_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.update_task.side_effect = TaskAccessDeniedException(task_id, user_id)
        payload = TaskUpdate(title="Updated")
        with pytest.raises(HTTPException) as exc_info:
            await controller.update_user_task(user_id, task_id, payload)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_update_user_task_validation_error(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.update_task.side_effect = TaskValidationError("Cannot strip")
        payload = TaskUpdate.model_construct(title="   ", description="   ")
        with pytest.raises(HTTPException) as exc_info:
            await controller.update_user_task(user_id, task_id, payload)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_delete_user_task_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.delete_task.return_value = None

        result = await controller.delete_user_task(user_id, task_id)
        assert result["status"] == "success"
        assert "trash" in result["message"]
        controller.service.delete_task.assert_called_once_with(user_id, task_id)

    async def test_delete_user_task_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.delete_task.side_effect = TaskNotFoundException(task_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.delete_user_task(user_id, task_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_user_task_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.delete_task.side_effect = TaskAccessDeniedException(task_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.delete_user_task(user_id, task_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_restore_user_task_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_task = self._make_task_response()
        controller.service.restore_task.return_value = mock_task

        result = await controller.restore_user_task(user_id, task_id)
        assert result.id == task_id
        controller.service.restore_task.assert_called_once_with(user_id, task_id)

    async def test_restore_user_task_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.restore_task.side_effect = TaskNotFoundException(task_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.restore_user_task(user_id, task_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_restore_user_task_already_active(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.restore_task.side_effect = TaskValidationError("already active")
        with pytest.raises(HTTPException) as exc_info:
            await controller.restore_user_task(user_id, task_id)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_restore_user_task_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.restore_task.side_effect = TaskAccessDeniedException(task_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.restore_user_task(user_id, task_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_archive_user_task_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_task = self._make_task_response()
        controller.service.toggle_archive_status.return_value = mock_task

        result = await controller.archive_user_task(user_id, task_id)
        assert result.is_archived is False
        controller.service.toggle_archive_status.assert_called_once_with(user_id, task_id, archive=True)

    async def test_archive_user_task_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_archive_status.side_effect = TaskNotFoundException(task_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.archive_user_task(user_id, task_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_archive_user_task_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_archive_status.side_effect = TaskAccessDeniedException(task_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.archive_user_task(user_id, task_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_unarchive_user_task_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_task = self._make_task_response()
        controller.service.toggle_archive_status.return_value = mock_task

        result = await controller.unarchive_user_task(user_id, task_id)
        controller.service.toggle_archive_status.assert_called_once_with(user_id, task_id, archive=False)

    async def test_unarchive_user_task_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_archive_status.side_effect = TaskNotFoundException(task_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.unarchive_user_task(user_id, task_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_unarchive_user_task_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_archive_status.side_effect = TaskAccessDeniedException(task_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.unarchive_user_task(user_id, task_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_pin_user_task_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_task = self._make_task_response()
        controller.service.toggle_pin_status.return_value = mock_task

        result = await controller.pin_user_task(user_id, task_id)
        controller.service.toggle_pin_status.assert_called_once_with(user_id, task_id, pin=True)

    async def test_pin_user_task_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_pin_status.side_effect = TaskNotFoundException(task_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.pin_user_task(user_id, task_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_pin_user_task_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_pin_status.side_effect = TaskAccessDeniedException(task_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.pin_user_task(user_id, task_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_unpin_user_task_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_task = self._make_task_response()
        controller.service.toggle_pin_status.return_value = mock_task

        result = await controller.unpin_user_task(user_id, task_id)
        controller.service.toggle_pin_status.assert_called_once_with(user_id, task_id, pin=False)

    async def test_unpin_user_task_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_pin_status.side_effect = TaskNotFoundException(task_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.unpin_user_task(user_id, task_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_unpin_user_task_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_pin_status.side_effect = TaskAccessDeniedException(task_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.unpin_user_task(user_id, task_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_favorite_user_task_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_task = self._make_task_response()
        controller.service.toggle_favorite_status.return_value = mock_task

        result = await controller.favorite_user_task(user_id, task_id)
        controller.service.toggle_favorite_status.assert_called_once_with(user_id, task_id, favorite=True)

    async def test_favorite_user_task_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_favorite_status.side_effect = TaskNotFoundException(task_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.favorite_user_task(user_id, task_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_favorite_user_task_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_favorite_status.side_effect = TaskAccessDeniedException(task_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.favorite_user_task(user_id, task_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_unfavorite_user_task_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_task = self._make_task_response()
        controller.service.toggle_favorite_status.return_value = mock_task

        result = await controller.unfavorite_user_task(user_id, task_id)
        controller.service.toggle_favorite_status.assert_called_once_with(user_id, task_id, favorite=False)

    async def test_unfavorite_user_task_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_favorite_status.side_effect = TaskNotFoundException(task_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.unfavorite_user_task(user_id, task_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_unfavorite_user_task_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_favorite_status.side_effect = TaskAccessDeniedException(task_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.unfavorite_user_task(user_id, task_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_get_analytics_delegates(self, controller):
        controller.service.get_analytics.return_value = {"total": 5}
        result = await controller.get_analytics(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert result["total"] == 5

    async def test_list_user_tasks_returns_list_response(self, controller):
        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_task = self._make_task_response()
        controller.service.list_and_filter_tasks.return_value = [mock_task]

        result = await controller.list_user_tasks(
            user_id=user_id,
            search=None,
            status_filter=None,
            priority=None,
            label=None,
            favorite=None,
            pinned=None,
            archived=False,
            deleted=False,
            due_date=None,
            sort_by="updated_at",
            sort_order="desc",
        )
        assert result.total_count == 1
        assert len(result.tasks) == 1
        assert result.tasks[0].title == "Test Task"

    async def test_get_task_history_timeline_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_history = {
            "id": uuid.UUID("12345678-1234-5678-1234-567812345678"),
            "action": "CREATED",
            "field_name": None,
            "old_value": None,
            "new_value": "Task",
            "created_at": datetime.now(timezone.utc),
            "user": {"id": user_id, "name": "John"},
        }
        controller.service.get_task_history.return_value = [mock_history]

        result = await controller.get_task_history_timeline(user_id, task_id)
        assert result.total_count == 1
        assert len(result.history) == 1
        assert result.history[0].action == "CREATED"

    async def test_get_task_history_timeline_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.get_task_history.side_effect = TaskNotFoundException(task_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.get_task_history_timeline(user_id, task_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_task_history_timeline_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.get_task_history.side_effect = TaskAccessDeniedException(task_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.get_task_history_timeline(user_id, task_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
