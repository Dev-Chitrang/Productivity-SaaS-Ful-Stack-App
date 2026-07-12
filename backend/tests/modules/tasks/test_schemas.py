import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
import pytest
from pydantic import ValidationError
from app.modules.tasks.enums import TaskStatus, TaskPriority
from app.modules.tasks.constants import MAX_TASK_TITLE_LENGTH
from app.modules.tasks.schemas import (
    ChecklistItem,
    TaskBase,
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    UserInfo,
    TaskHistoryResponse,
    TaskHistoryListResponse,
)


class TestChecklistItem:
    def test_valid_item(self):
        item = ChecklistItem(id="1", text="Buy milk", completed=False)
        assert item.id == "1"
        assert item.text == "Buy milk"
        assert item.completed is False

    def test_completed_defaults_false(self):
        item = ChecklistItem(id="1", text="Buy milk")
        assert item.completed is False

    def test_empty_text_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            ChecklistItem(id="1", text="   ")

    def test_strips_whitespace(self):
        item = ChecklistItem(id="1", text="  Buy milk  ")
        assert item.text == "Buy milk"


class TestTaskBase:
    def test_valid_base(self):
        now = datetime.now(timezone.utc)
        model = TaskBase(
            title="Buy groceries",
            description={"type": "doc", "content": []},
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            due_date=now + timedelta(days=1),
            labels=["work", "personal"],
            checklist=[{"id": "1", "text": "Milk", "completed": False}],
            is_pinned=True,
            is_favorite=False,
            is_archived=False,
        )
        assert model.title == "Buy groceries"
        assert model.status == TaskStatus.IN_PROGRESS
        assert model.priority == TaskPriority.HIGH
        assert len(model.labels) == 2
        assert len(model.checklist) == 1

    def test_title_strips_whitespace(self):
        model = TaskBase(title="  Buy groceries  ", description=None)
        assert model.title == "Buy groceries"

    def test_empty_title_raises(self):
        with pytest.raises(ValidationError, match="cannot be blank"):
            TaskBase(title="   ", description={"type": "doc", "content": []})

    def test_title_max_length(self):
        title = "a" * MAX_TASK_TITLE_LENGTH
        model = TaskBase(title=title, description=None)
        assert len(model.title) == MAX_TASK_TITLE_LENGTH

    def test_title_exceeds_max_length(self):
        title = "a" * (MAX_TASK_TITLE_LENGTH + 1)
        with pytest.raises(ValidationError):
            TaskBase(title=title, description=None)

    def test_labels_deduplicate_and_lower(self):
        model = TaskBase(
            title="Task",
            description=None,
            labels=["Work", "work", "Personal"],
        )
        assert "work" in model.labels
        assert "personal" in model.labels
        assert len(model.labels) == 2

    def test_labels_empty_list_default(self):
        model = TaskBase(title="Task", description=None)
        assert model.labels == []

    def test_checklist_default_empty(self):
        model = TaskBase(title="Task", description=None)
        assert model.checklist == []

    def test_default_status_todo(self):
        model = TaskBase(title="Task", description=None)
        assert model.status == TaskStatus.TODO

    def test_default_priority_medium(self):
        model = TaskBase(title="Task", description=None)
        assert model.priority == TaskPriority.MEDIUM

    def test_default_flags_false(self):
        model = TaskBase(title="Task", description=None)
        assert model.is_pinned is False
        assert model.is_favorite is False
        assert model.is_archived is False


class TestTaskCreate:
    def test_valid_create(self):
        now = datetime.now(timezone.utc)
        model = TaskCreate(
            title="Buy groceries",
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
        assert model.title == "Buy groceries"

    def test_past_due_date_raises(self):
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError, match="due_date cannot be set in the past"):
            TaskCreate(
                title="Past Task",
                description=None,
                due_date=now - timedelta(days=1),
            )

    def test_today_due_date_allowed(self):
        now = datetime.now(timezone.utc)
        model = TaskCreate(
            title="Today Task",
            description=None,
            due_date=now.replace(hour=23, minute=59, second=59, microsecond=0),
        )
        assert model.due_date is not None

    def test_future_due_date_allowed(self):
        now = datetime.now(timezone.utc)
        model = TaskCreate(
            title="Future Task",
            description=None,
            due_date=now + timedelta(days=1),
        )
        assert model.due_date is not None

    def test_no_due_date_allowed(self):
        model = TaskCreate(title="No Due Date", description=None)
        assert model.due_date is None

    def test_checklist_with_items(self):
        model = TaskCreate(
            title="Task with checklist",
            description=None,
            checklist=[
                {"id": "1", "text": "Step 1", "completed": False},
                {"id": "2", "text": "Step 2", "completed": True},
            ],
        )
        assert len(model.checklist) == 2
        assert model.checklist[0].id == "1"
        assert model.checklist[1].completed is True


class TestTaskUpdate:
    def test_valid_partial_update(self):
        model = TaskUpdate(
            title="Updated Task",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
        )
        assert model.title == "Updated Task"
        assert model.status == TaskStatus.IN_PROGRESS
        assert model.description is None

    def test_all_fields_optional(self):
        model = TaskUpdate()
        assert model.title is None
        assert model.description is None
        assert model.status is None
        assert model.priority is None
        assert model.due_date is None
        assert model.labels is None
        assert model.checklist is None

    def test_empty_title_raises(self):
        with pytest.raises(ValidationError, match="cannot be updated to an empty string"):
            TaskUpdate(title="   ")

    def test_valid_title_preserves_whitespace(self):
        model = TaskUpdate(title="  Updated  ")
        assert model.title == "  Updated  "

    def test_update_labels(self):
        model = TaskUpdate(labels=["new", "labels"])
        assert model.labels is not None
        assert len(model.labels) == 2

    def test_update_checklist(self):
        model = TaskUpdate(checklist=[{"id": "1", "text": "New item", "completed": True}])
        assert len(model.checklist) == 1
        assert model.checklist[0].completed is True

    def test_update_due_date(self):
        now = datetime.now(timezone.utc)
        model = TaskUpdate(due_date=now + timedelta(days=1))
        assert model.due_date is not None


class TestTaskResponse:
    def test_valid_response(self):
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        now = datetime.now(timezone.utc)
        data = {
            "id": task_id,
            "user_id": user_id,
            "title": "Task",
            "description": None,
            "status": TaskStatus.TODO,
            "priority": TaskPriority.MEDIUM,
            "due_date": now + timedelta(days=1),
            "labels": [],
            "checklist": [],
            "is_pinned": False,
            "is_favorite": False,
            "is_archived": False,
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
        }
        model = TaskResponse(**data)
        assert model.id == task_id
        assert model.user_id == user_id
        assert model.title == "Task"

    def test_from_attributes_config(self):
        assert TaskResponse.model_config.get("from_attributes") is True


class TestTaskListResponse:
    def test_valid_list(self):
        now = datetime.now(timezone.utc)
        task = TaskResponse(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            user_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            title="Task",
            description=None,
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            due_date=None,
            labels=[],
            checklist=[],
            is_pinned=False,
            is_favorite=False,
            is_archived=False,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )
        model = TaskListResponse(tasks=[task], total_count=1)
        assert len(model.tasks) == 1
        assert model.total_count == 1

    def test_empty_list(self):
        model = TaskListResponse(tasks=[], total_count=0)
        assert model.tasks == []
        assert model.total_count == 0


class TestUserInfo:
    def test_valid(self):
        model = UserInfo(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            name="John Doe",
        )
        assert model.id == uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert model.name == "John Doe"

    def test_from_attributes_config(self):
        assert UserInfo.model_config.get("from_attributes") is True


class TestTaskHistoryResponse:
    def test_valid(self):
        now = datetime.now(timezone.utc)
        model = TaskHistoryResponse(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            action="UPDATED",
            field_name="status",
            old_value="TODO",
            new_value="IN_PROGRESS",
            created_at=now,
            user=UserInfo(
                id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
                name="John",
            ),
        )
        assert model.action == "UPDATED"
        assert model.field_name == "status"
        assert model.old_value == "TODO"
        assert model.new_value == "IN_PROGRESS"
        assert model.user.name == "John"


class TestTaskHistoryListResponse:
    def test_valid_list(self):
        now = datetime.now(timezone.utc)
        history = TaskHistoryResponse(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            action="CREATED",
            field_name=None,
            old_value=None,
            new_value=None,
            created_at=now,
            user=UserInfo(
                id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
                name="John",
            ),
        )
        model = TaskHistoryListResponse(history=[history], total_count=1)
        assert len(model.history) == 1
        assert model.total_count == 1
