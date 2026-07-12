import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from app.modules.tasks.enums import TaskStatus, TaskPriority
from app.models.tasks import Task, TaskHistory


class TestTaskModel:
    def test_tablename(self):
        assert Task.__tablename__ == "tasks"

    def test_id_default_generates_uuid(self):
        task = Task(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Test Task",
        )
        assert task.id is None or isinstance(task.id, (uuid.UUID, type(uuid.uuid7())))

    def test_minimal_fields(self):
        now = datetime.now(timezone.utc)
        task = Task(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Minimal Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            labels=[],
            checklist=[],
            is_pinned=False,
            is_favorite=False,
            is_archived=False,
            created_at=now,
            updated_at=now,
        )
        assert task.user_id == uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert task.title == "Minimal Task"
        assert task.description is None
        assert task.status == TaskStatus.TODO
        assert task.priority == TaskPriority.MEDIUM
        assert task.due_date is None
        assert task.labels == []
        assert task.checklist == []
        assert task.is_pinned is False
        assert task.is_favorite is False
        assert task.is_archived is False
        assert task.deleted_at is None
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)

    def test_full_fields(self):
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        now = datetime.now(timezone.utc)
        task = Task(
            id=task_id,
            user_id=user_id,
            title="Full Task",
            description={"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Desc"}]}]},
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            due_date=now,
            labels=["work", "urgent"],
            checklist=[{"id": "1", "text": "Item 1", "completed": False}],
            is_pinned=True,
            is_favorite=True,
            is_archived=False,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )
        assert task.id == task_id
        assert task.user_id == user_id
        assert task.title == "Full Task"
        assert task.description is not None
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.HIGH
        assert task.due_date == now
        assert task.labels == ["work", "urgent"]
        assert len(task.checklist) == 1
        assert task.is_pinned is True
        assert task.is_favorite is True

    def test_soft_delete(self):
        now = datetime.now(timezone.utc)
        task = Task(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Delete me",
            deleted_at=now,
        )
        assert task.deleted_at == now

    def test_created_at_default_utc(self):
        now = datetime.now(timezone.utc)
        task = Task(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Task",
            created_at=now,
        )
        assert task.created_at is not None
        assert task.created_at.tzinfo == timezone.utc

    def test_updated_at_default_utc(self):
        now = datetime.now(timezone.utc)
        task = Task(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Task",
            updated_at=now,
        )
        assert task.updated_at is not None
        assert task.updated_at.tzinfo == timezone.utc


class TestTaskHistoryModel:
    def test_tablename(self):
        assert TaskHistory.__tablename__ == "task_history"

    def test_id_default_generates_uuid(self):
        history = TaskHistory(
            task_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            user_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            action="CREATED",
        )
        assert history.id is None or isinstance(history.id, (uuid.UUID, type(uuid.uuid7())))

    def test_minimal_fields(self):
        now = datetime.now(timezone.utc)
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        history = TaskHistory(
            task_id=task_id,
            user_id=user_id,
            action="UPDATED",
            created_at=now,
        )
        assert history.task_id == task_id
        assert history.user_id == user_id
        assert history.action == "UPDATED"
        assert history.field_name is None
        assert history.old_value is None
        assert history.new_value is None
        assert isinstance(history.created_at, datetime)

    def test_full_fields(self):
        now = datetime.now(timezone.utc)
        history = TaskHistory(
            task_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            user_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            action="UPDATED",
            field_name="status",
            old_value="TODO",
            new_value="DONE",
            created_at=now,
        )
        assert history.field_name == "status"
        assert history.old_value == "TODO"
        assert history.new_value == "DONE"
        assert history.created_at == now

    def test_created_at_default_utc(self):
        now = datetime.now(timezone.utc)
        history = TaskHistory(
            task_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            user_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            action="CREATED",
            created_at=now,
        )
        assert history.created_at is not None
        assert history.created_at.tzinfo == timezone.utc
