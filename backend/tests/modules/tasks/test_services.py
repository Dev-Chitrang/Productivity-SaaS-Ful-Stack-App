import uuid
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.modules.tasks.exceptions import (
    TaskNotFoundException,
    TaskAccessDeniedException,
    TaskValidationError,
)
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.services import TaskService
from app.modules.tasks.schemas import TaskCreate, TaskUpdate, ChecklistItem
from app.modules.tasks.enums import TaskStatus, TaskPriority
from app.models.tasks import Task


@pytest.fixture
def repo():
    mock = MagicMock(spec=TaskRepository)
    async def execute(stmt):
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        return result
    mock.db = AsyncMock()
    mock.db.execute = execute
    return mock


@pytest.fixture
def service(repo):
    return TaskService(repo, attachment_service=None)


def _make_task(**kwargs):
    now = datetime.now(timezone.utc)
    return Task(
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
        deleted_at=kwargs.get("deleted_at", None),
        created_at=kwargs.get("created_at", now),
        updated_at=kwargs.get("updated_at", now),
    )


class TestGetTask:
    async def test_get_task_success(self, service, repo):
        task = _make_task()
        repo.get_by_id.return_value = task

        result = await service.get_task(task.user_id, task.id)
        assert result == task
        repo.get_by_id.assert_called_once_with(task.id, include_deleted=False)

    async def test_get_task_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(TaskNotFoundException):
            await service.get_task(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"))

    async def test_get_task_access_denied(self, service, repo):
        task = _make_task(user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"))
        repo.get_by_id.return_value = task
        with pytest.raises(TaskAccessDeniedException):
            await service.get_task(uuid.UUID("87654321-4321-8765-4321-876543218765"), task.id)

    async def test_get_task_includes_deleted_when_flag_true(self, service, repo):
        task = _make_task(deleted_at=datetime.now(timezone.utc))
        repo.get_by_id.return_value = task

        result = await service.get_task(task.user_id, task.id, include_deleted=True)
        assert result == task
        repo.get_by_id.assert_called_once_with(task.id, include_deleted=True)


class TestGetTaskHistory:
    async def test_get_task_history_success(self, service, repo):
        task = _make_task()
        repo.get_by_id.return_value = task
        repo.get_history_by_task_id.return_value = []

        result = await service.get_task_history(task.user_id, task.id)
        repo.get_history_by_task_id.assert_called_once_with(task.id)

    async def test_get_task_history_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(TaskNotFoundException):
            await service.get_task_history(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"))


class TestCreateTask:
    async def test_create_task_success(self, service, repo):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        now = datetime.now(timezone.utc)
        payload = TaskCreate(
            title="New Task",
            description=None,
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            due_date=now + timedelta(days=1),
            labels=["work"],
            checklist=[],
            is_pinned=False,
            is_favorite=False,
            is_archived=False,
        )
        repo.create.return_value = _make_task()

        result = await service.create_task(user_id, payload)
        repo.create.assert_called_once()
        repo.create_history_bulk.assert_called_once()

    async def test_create_task_past_due_date_raises(self, service):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        now = datetime.now(timezone.utc)
        payload = TaskCreate.model_construct(
            title="Past Task",
            description=None,
            due_date=now - timedelta(days=1),
        )
        with pytest.raises(TaskValidationError, match="past"):
            await service.create_task(user_id, payload)

    async def test_create_task_today_due_date_allowed(self, service, repo):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        now = datetime.now(timezone.utc)
        payload = TaskCreate(
            title="Today Task",
            description=None,
            due_date=now.replace(hour=23, minute=59, second=59, microsecond=0),
        )
        repo.create.return_value = _make_task()
        result = await service.create_task(user_id, payload)
        repo.create.assert_called_once()


class TestUpdateTask:
    async def test_update_task_success(self, service, repo):
        task = _make_task()
        repo.get_by_id.return_value = task
        repo.update.return_value = task

        payload = TaskUpdate(title="Updated Title", status=TaskStatus.IN_PROGRESS)
        result = await service.update_task(task.user_id, task.id, payload)
        repo.update.assert_called_once()
        repo.create_history_bulk.assert_called_once()

    async def test_update_task_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        payload = TaskUpdate(title="Updated")
        with pytest.raises(TaskNotFoundException):
            await service.update_task(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"), payload)

    async def test_update_task_access_denied(self, service, repo):
        task = _make_task(user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"))
        repo.get_by_id.return_value = task
        payload = TaskUpdate(title="Updated")
        with pytest.raises(TaskAccessDeniedException):
            await service.update_task(uuid.UUID("87654321-4321-8765-4321-876543218765"), task.id, payload)

    async def test_update_task_past_due_date_raises(self, service, repo):
        task = _make_task()
        repo.get_by_id.return_value = task

        past = datetime.now(timezone.utc) - timedelta(days=1)
        payload = TaskUpdate.model_construct(due_date=past)
        with pytest.raises(TaskValidationError, match="past"):
            await service.update_task(task.user_id, task.id, payload)

    async def test_update_task_tracks_changes(self, service, repo):
        task = _make_task()
        repo.get_by_id.return_value = task
        repo.update.return_value = task

        payload = TaskUpdate(title="New Title", status=TaskStatus.DONE)
        await service.update_task(task.user_id, task.id, payload)
        repo.create_history_bulk.assert_called_once()
        history = repo.create_history_bulk.call_args[0][0]
        assert len(history) == 2
        field_names = [h["field_name"] for h in history]
        assert "title" in field_names
        assert "status" in field_names


class TestDeleteTask:
    async def test_delete_task_success_without_attachments(self, service, repo):
        task = _make_task()
        repo.get_by_id.return_value = task

        await service.delete_task(task.user_id, task.id)
        repo.soft_delete.assert_called_once_with(task)
        repo.create_history_bulk.assert_called_once()

    async def test_delete_task_cascades_to_attachments(self, service, repo):
        task = _make_task()
        repo.get_by_id.return_value = task
        attachment_service = AsyncMock()
        service_with_att = TaskService(repo, attachment_service=attachment_service)

        await service_with_att.delete_task(task.user_id, task.id)
        repo.soft_delete.assert_called_once_with(task)

    async def test_delete_task_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(TaskNotFoundException):
            await service.delete_task(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"))

    async def test_delete_task_access_denied(self, service, repo):
        task = _make_task(user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"))
        repo.get_by_id.return_value = task
        with pytest.raises(TaskAccessDeniedException):
            await service.delete_task(uuid.UUID("87654321-4321-8765-4321-876543218765"), task.id)


class TestRestoreTask:
    async def test_restore_task_success(self, service, repo):
        task = _make_task(deleted_at=datetime.now(timezone.utc))
        repo.get_by_id.return_value = task

        async def _do_restore(t):
            t.deleted_at = None
            return t
        repo.restore.side_effect = _do_restore

        result = await service.restore_task(task.user_id, task.id)
        assert result.deleted_at is None
        repo.restore.assert_called_once_with(task)
        repo.create_history_bulk.assert_called_once()

    async def test_restore_task_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(TaskNotFoundException):
            await service.restore_task(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"))

    async def test_restore_task_already_active_raises(self, service, repo):
        task = _make_task(deleted_at=None)
        repo.get_by_id.return_value = task
        with pytest.raises(TaskValidationError, match="already active"):
            await service.restore_task(task.user_id, task.id)

    async def test_restore_task_access_denied(self, service, repo):
        task = _make_task(user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"), deleted_at=datetime.now(timezone.utc))
        repo.get_by_id.return_value = task
        with pytest.raises(TaskAccessDeniedException):
            await service.restore_task(uuid.UUID("87654321-4321-8765-4321-876543218765"), task.id)


class TestToggleArchiveStatus:
    async def test_archive_task_success(self, service, repo):
        task = _make_task()
        repo.get_by_id.return_value = task
        repo.update.return_value = task

        result = await service.toggle_archive_status(task.user_id, task.id, archive=True)
        repo.update.assert_called_once_with(task, {"is_archived": True})
        repo.create_history_bulk.assert_called_once()

    async def test_unarchive_task_success(self, service, repo):
        task = _make_task()
        repo.get_by_id.return_value = task
        repo.update.return_value = task

        result = await service.toggle_archive_status(task.user_id, task.id, archive=False)
        repo.update.assert_called_once_with(task, {"is_archived": False})
        repo.create_history_bulk.assert_called_once()

    async def test_archive_task_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(TaskNotFoundException):
            await service.toggle_archive_status(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"), archive=True)


class TestTogglePinStatus:
    async def test_pin_task_success(self, service, repo):
        task = _make_task()
        repo.get_by_id.return_value = task
        repo.update.return_value = task

        result = await service.toggle_pin_status(task.user_id, task.id, pin=True)
        repo.update.assert_called_once_with(task, {"is_pinned": True})
        repo.create_history_bulk.assert_called_once()

    async def test_unpin_task_success(self, service, repo):
        task = _make_task()
        repo.get_by_id.return_value = task
        repo.update.return_value = task

        result = await service.toggle_pin_status(task.user_id, task.id, pin=False)
        repo.update.assert_called_once_with(task, {"is_pinned": False})
        repo.create_history_bulk.assert_called_once()

    async def test_pin_task_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(TaskNotFoundException):
            await service.toggle_pin_status(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"), pin=True)


class TestToggleFavoriteStatus:
    async def test_favorite_task_success(self, service, repo):
        task = _make_task()
        repo.get_by_id.return_value = task
        repo.update.return_value = task

        result = await service.toggle_favorite_status(task.user_id, task.id, favorite=True)
        repo.update.assert_called_once_with(task, {"is_favorite": True})
        repo.create_history_bulk.assert_called_once()

    async def test_unfavorite_task_success(self, service, repo):
        task = _make_task()
        repo.get_by_id.return_value = task
        repo.update.return_value = task

        result = await service.toggle_favorite_status(task.user_id, task.id, favorite=False)
        repo.update.assert_called_once_with(task, {"is_favorite": False})
        repo.create_history_bulk.assert_called_once()

    async def test_favorite_task_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(TaskNotFoundException):
            await service.toggle_favorite_status(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"), favorite=True)


class TestGetAnalytics:
    async def test_get_analytics_delegates_to_repo(self, service, repo):
        repo.get_analytics.return_value = {"total": 5}
        result = await service.get_analytics(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert result["total"] == 5
        repo.get_analytics.assert_called_once()


class TestListAndFilterTasks:
    async def test_list_defaults_to_not_deleted(self, service, repo):
        repo.list_and_filter.return_value = []
        result = await service.list_and_filter_tasks(uuid.UUID("87654321-4321-8765-4321-876543218765"))
        repo.list_and_filter.assert_called_once_with(
            user_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            search=None,
            status=None,
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

    async def test_list_with_filters(self, service, repo):
        repo.list_and_filter.return_value = []
        now = datetime.now(timezone.utc)
        await service.list_and_filter_tasks(
            user_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            search="meeting",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            label="work",
            favorite=True,
            pinned=False,
            archived=False,
            deleted=False,
            due_date=now,
            sort_by="created_at",
            sort_order="asc",
        )
        repo.list_and_filter.assert_called_once()

    async def test_list_invalid_sort_falls_back_to_updated_at(self, service, repo):
        repo.list_and_filter.return_value = []
        await service.list_and_filter_tasks(
            user_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            sort_by="malicious_column",
        )
        call_kwargs = repo.list_and_filter.call_args[1]
        assert call_kwargs["sort_by"] == "updated_at"
