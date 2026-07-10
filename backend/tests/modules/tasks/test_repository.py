import uuid
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.tasks.repository import TaskRepository
from app.models.tasks import Task, TaskHistory
from app.modules.tasks.enums import TaskStatus, TaskPriority


@pytest.fixture
def repo():
    db = AsyncMock(spec=AsyncSession)
    return TaskRepository(db)


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


class TestTaskRepositoryCreate:
    async def test_create_success(self, repo):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        task_data = {"title": "New Task", "status": TaskStatus.TODO, "labels": ["work"]}
        result = await repo.create(user_id, task_data)
        assert result.user_id == user_id
        assert result.title == "New Task"
        repo.db.add.assert_called_once()
        repo.db.flush.assert_called_once()

    async def test_create_rollback_on_exception(self, repo):
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.create(uuid.UUID("87654321-4321-8765-4321-876543218765"), {"title": "x"})
        repo.db.rollback.assert_called_once()


class TestTaskRepositoryGetById:
    async def test_get_by_id_found(self, repo):
        task = _make_task()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = task
        repo.db.execute.return_value = result_mock

        found = await repo.get_by_id(task.id)
        assert found == task

    async def test_get_by_id_not_found(self, repo):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        repo.db.execute.return_value = result_mock

        found = await repo.get_by_id(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert found is None

    async def test_get_by_id_excludes_soft_deleted_by_default(self, repo):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        repo.db.execute.return_value = result_mock

        await repo.get_by_id(uuid.UUID("12345678-1234-5678-1234-567812345678"), include_deleted=False)
        stmt = repo.db.execute.call_args[0][0]
        assert "deleted_at" in str(stmt)

    async def test_get_by_id_includes_deleted_when_requested(self, repo):
        task = _make_task(deleted_at=datetime.now(timezone.utc))
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = task
        repo.db.execute.return_value = result_mock

        found = await repo.get_by_id(task.id, include_deleted=True)
        assert found == task


class TestTaskRepositoryUpdate:
    async def test_update_success(self, repo):
        task = _make_task()
        update_data = {"title": "Updated", "status": TaskStatus.DONE}
        result = await repo.update(task, update_data)
        assert result.title == "Updated"
        assert result.status == TaskStatus.DONE
        repo.db.add.assert_called_once_with(task)
        repo.db.flush.assert_called_once()

    async def test_update_partial_fields(self, repo):
        task = _make_task()
        update_data = {"title": "Updated"}
        result = await repo.update(task, update_data)
        assert result.title == "Updated"
        assert result.status == TaskStatus.TODO

    async def test_update_rollback_on_exception(self, repo):
        task = _make_task()
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.update(task, {"title": "Updated"})
        repo.db.rollback.assert_called_once()


class TestTaskRepositorySoftDelete:
    async def test_soft_delete_success(self, repo):
        task = _make_task(deleted_at=None)
        now = datetime.now(timezone.utc)
        result = await repo.soft_delete(task)
        assert result is None
        assert task.deleted_at is not None
        assert task.deleted_at >= now - timedelta(seconds=2)
        repo.db.add.assert_called_once_with(task)
        repo.db.flush.assert_called_once()

    async def test_soft_delete_rollback_on_exception(self, repo):
        task = _make_task()
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.soft_delete(task)
        repo.db.rollback.assert_called_once()


class TestTaskRepositoryRestore:
    async def test_restore_success(self, repo):
        task = _make_task(deleted_at=datetime.now(timezone.utc))
        result = await repo.restore(task)
        assert result.deleted_at is None
        repo.db.add.assert_called_once_with(task)
        repo.db.flush.assert_called_once()

    async def test_restore_rollback_on_exception(self, repo):
        task = _make_task(deleted_at=datetime.now(timezone.utc))
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.restore(task)
        repo.db.rollback.assert_called_once()


class TestTaskRepositoryGetAnalytics:
    async def test_get_analytics_returns_dict(self, repo):
        repo.db.scalar.return_value = 5
        repo.db.execute.return_value = MagicMock()

        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        result = await repo.get_analytics(user_id)

        assert "total" in result
        assert "today" in result
        assert "overdue" in result
        assert "upcoming" in result
        assert "priority_distribution" in result
        assert "status_distribution" in result
        assert "due_today" in result
        assert "overdue_tasks" in result

    async def test_get_analytics_counts(self, repo):
        repo.db.scalar.side_effect = [10, 2, 1, 5]
        repo.db.execute.return_value = MagicMock()

        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        result = await repo.get_analytics(user_id)

        assert result["total"] == 10
        assert result["today"] == 2
        assert result["overdue"] == 1
        assert result["upcoming"] == 5

    async def test_get_analytics_due_today_structure(self, repo):
        repo.db.scalar.return_value = 0
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        result = await repo.get_analytics(user_id)

        assert isinstance(result["due_today"], list)
        assert isinstance(result["overdue_tasks"], list)


class TestTaskRepositoryListAndFilter:
    async def test_list_returns_sequence(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        result = await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"))
        assert isinstance(result, list)

    async def test_list_filters_by_user(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"))
        stmt = repo.db.execute.call_args[0][0]
        assert "user_id" in str(stmt)

    async def test_list_excludes_deleted_by_default(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"))
        stmt = repo.db.execute.call_args[0][0]
        assert "deleted_at" in str(stmt)

    async def test_list_includes_deleted_when_true(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), deleted=True)
        stmt = repo.db.execute.call_args[0][0]
        assert "deleted_at" in str(stmt)

    async def test_list_status_filter_in_query(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), status=TaskStatus.IN_PROGRESS)
        stmt = repo.db.execute.call_args[0][0]
        assert "status" in str(stmt)

    async def test_list_status_filter(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), status=TaskStatus.IN_PROGRESS)
        stmt = repo.db.execute.call_args[0][0]
        assert "status" in str(stmt)

    async def test_list_priority_filter(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), priority=TaskPriority.HIGH)
        stmt = repo.db.execute.call_args[0][0]
        assert "priority" in str(stmt)

    async def test_list_label_filter(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), label="work")
        stmt = repo.db.execute.call_args[0][0]
        assert "labels" in str(stmt).lower()
        assert "@>" in str(stmt)

    async def test_list_favorite_filter(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), favorite=True)
        stmt = repo.db.execute.call_args[0][0]
        assert "is_favorite" in str(stmt)

    async def test_list_pinned_filter(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), pinned=True)
        stmt = repo.db.execute.call_args[0][0]
        assert "is_pinned" in str(stmt)

    async def test_list_archived_filter(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), archived=True)
        stmt = repo.db.execute.call_args[0][0]
        assert "is_archived" in str(stmt)

    async def test_list_sort_by_updated_at_desc(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), sort_by="updated_at", sort_order="desc")
        stmt = repo.db.execute.call_args[0][0]
        assert "updated_at" in str(stmt)

    async def test_list_sort_by_title_asc(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), sort_by="title", sort_order="asc")
        stmt = repo.db.execute.call_args[0][0]
        assert "title" in str(stmt)

    async def test_list_invalid_sort_falls_back_to_updated_at(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), sort_by="invalid_column")
        stmt = repo.db.execute.call_args[0][0]
        assert "updated_at" in str(stmt)

    async def test_list_priority_sort_uses_case_statement(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), sort_by="priority", sort_order="asc")
        stmt = repo.db.execute.call_args[0][0]
        assert "case" in str(stmt).lower()


class TestTaskRepositoryCreateHistoryBulk:
    async def test_create_history_bulk_success(self, repo):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        history_records = [
            {
                "task_id": uuid.UUID("12345678-1234-5678-1234-567812345678"),
                "user_id": user_id,
                "action": "CREATED",
                "field_name": None,
                "old_value": None,
                "new_value": "Task",
            }
        ]
        await repo.create_history_bulk(history_records)
        repo.db.add.assert_called_once()
        repo.db.flush.assert_called_once()

    async def test_create_history_bulk_empty_list(self, repo):
        await repo.create_history_bulk([])
        repo.db.add.assert_not_called()
        repo.db.flush.assert_not_called()

    async def test_create_history_bulk_rollback_on_exception(self, repo):
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.create_history_bulk([
                {
                    "task_id": uuid.UUID("12345678-1234-5678-1234-567812345678"),
                    "user_id": uuid.UUID("87654321-4321-8765-4321-876543218765"),
                    "action": "CREATED",
                }
            ])
        repo.db.rollback.assert_called_once()


class TestTaskRepositoryGetHistoryByTaskId:
    async def test_get_history_returns_sequence(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.all.return_value = []

        result = await repo.get_history_by_task_id(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert isinstance(result, list)

    async def test_get_history_includes_join_with_user(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.all.return_value = []

        await repo.get_history_by_task_id(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        stmt = repo.db.execute.call_args[0][0]
        assert "task_history" in str(stmt).lower()
        assert "user" in str(stmt).lower()
