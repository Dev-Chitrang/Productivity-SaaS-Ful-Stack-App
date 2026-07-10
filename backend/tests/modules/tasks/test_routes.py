import uuid
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.main import app
from app.core.database import get_db
from app.core.redis import get_redis_client
from app.modules.tasks.dependencies import (
    get_current_user_id,
    get_tasks_service,
    get_attachment_service,
)
from app.modules.tasks.controller import TaskController
from app.modules.tasks.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
)
from app.modules.tasks.enums import TaskStatus, TaskPriority
from app.modules.tasks.exceptions import TaskAccessDeniedException
from app.modules.tasks.services import TaskService
from app.modules.attachments.schemas import AttachmentListResponse, AttachmentResponse


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_redis():
    mock = AsyncMock(spec=Redis)
    mock_pipeline = AsyncMock()
    mock_pipeline.zremrangebyscore = MagicMock()
    mock_pipeline.zcard = MagicMock()
    mock_pipeline.zrange = MagicMock()
    mock_pipeline.zadd = MagicMock()
    mock_pipeline.expire = MagicMock()
    mock_pipeline.execute = AsyncMock(return_value=[0, 0, []])
    mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
    mock_pipeline.__aexit__ = AsyncMock(return_value=False)
    mock.pipeline.return_value = mock_pipeline
    return mock


@pytest.fixture
def override_deps(mock_db, mock_redis):
    def _get_db():
        return mock_db

    def _get_redis():
        return mock_redis

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_redis_client] = _get_redis
    yield
    app.dependency_overrides.clear()


def _mock_current_user_id():
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


def _make_task_response(**kwargs):
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


class TestTaskRoutes:
    async def test_create_task_success(self, client, override_deps):
        mock_service = MagicMock(spec=TaskService)
        mock_task = _make_task_response()
        mock_service.create_task.return_value = mock_task

        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_tasks_service] = lambda: mock_service
        response = client.post(
            "/api/v1/tasks",
            json={
                "title": "New Task",
                "description": None,
                "status": "TODO",
                "priority": "MEDIUM",
            },
        )
        assert response.status_code == 201
        assert response.json()["title"] == "Test Task"

    async def test_create_task_empty_title_raises(self, client, override_deps):
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_tasks_service] = lambda: MagicMock(spec=TaskService)
        response = client.post(
            "/api/v1/tasks",
            json={"title": "   ", "description": None},
        )
        assert response.status_code == 422

    async def test_list_tasks_success(self, client, override_deps):
        mock_service = MagicMock(spec=TaskService)
        mock_service.list_and_filter_tasks.return_value = [_make_task_response()]

        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_tasks_service] = lambda: mock_service
        response = client.get("/api/v1/tasks")
        assert response.status_code == 200
        assert response.json()["total_count"] == 1

    async def test_list_tasks_with_filters(self, client, override_deps):
        mock_service = MagicMock(spec=TaskService)
        mock_service.list_and_filter_tasks.return_value = []

        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_tasks_service] = lambda: mock_service
        response = client.get(
            "/api/v1/tasks",
            params={
                "search": "meeting",
                "status": "IN PROGRESS",
                "priority": "HIGH",
                "label": "work",
                "favorite": "true",
                "pinned": "false",
                "archived": "false",
                "deleted": "false",
                "due_date": datetime.now(timezone.utc).isoformat(),
                "sort_by": "created_at",
                "sort_order": "asc",
            },
        )
        assert response.status_code == 200

    async def test_get_analytics_success(self, client, override_deps):
        mock_service = MagicMock(spec=TaskService)
        mock_service.get_analytics.return_value = {"total": 5, "today": 1}

        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_tasks_service] = lambda: mock_service
        response = client.get("/api/v1/tasks/analytics")
        assert response.status_code == 200
        assert response.json()["total"] == 5

    async def test_get_task_success(self, client, override_deps):
        mock_service = MagicMock(spec=TaskService)
        mock_task = _make_task_response()
        mock_service.get_task.return_value = mock_task

        task_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_tasks_service] = lambda: mock_service
        response = client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["id"] == task_id

    async def test_get_task_access_denied(self, client, override_deps):
        mock_service = MagicMock(spec=TaskService)
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_service.get_task.side_effect = TaskAccessDeniedException(task_id, uuid.UUID("87654321-4321-8765-4321-876543218765"))

        task_id = str(task_id)
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_tasks_service] = lambda: mock_service
        response = client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 403

    async def test_update_task_success(self, client, override_deps):
        mock_service = MagicMock(spec=TaskService)
        mock_task = _make_task_response(title="Updated")
        mock_service.update_task.return_value = mock_task

        task_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_tasks_service] = lambda: mock_service
        response = client.patch(
            f"/api/v1/tasks/{task_id}",
            json={"title": "Updated"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated"

    async def test_delete_task_success(self, client, override_deps):
        mock_service = MagicMock(spec=TaskService)
        mock_service.delete_task.return_value = None

        task_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_tasks_service] = lambda: mock_service
        response = client.delete(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        assert "trash" in response.json()["message"]

    async def test_restore_task_success(self, client, override_deps):
        mock_service = MagicMock(spec=TaskService)
        mock_task = _make_task_response()
        mock_service.restore_task.return_value = mock_task

        task_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_tasks_service] = lambda: mock_service
        response = client.patch(f"/api/v1/tasks/{task_id}/restore")
        assert response.status_code == 200
        assert response.json()["id"] == task_id

    async def test_archive_task_success(self, client, override_deps):
        mock_service = MagicMock(spec=TaskService)
        mock_task = _make_task_response()
        mock_service.toggle_archive_status.return_value = mock_task

        task_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_tasks_service] = lambda: mock_service
        response = client.patch(f"/api/v1/tasks/{task_id}/archive")
        assert response.status_code == 200

    async def test_unarchive_task_success(self, client, override_deps):
        mock_service = MagicMock(spec=TaskService)
        mock_task = _make_task_response()
        mock_service.toggle_archive_status.return_value = mock_task

        task_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_tasks_service] = lambda: mock_service
        response = client.patch(f"/api/v1/tasks/{task_id}/unarchive")
        assert response.status_code == 200

    async def test_pin_task_success(self, client, override_deps):
        mock_service = MagicMock(spec=TaskService)
        mock_task = _make_task_response()
        mock_service.toggle_pin_status.return_value = mock_task

        task_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_tasks_service] = lambda: mock_service
        response = client.patch(f"/api/v1/tasks/{task_id}/pin")
        assert response.status_code == 200

    async def test_unpin_task_success(self, client, override_deps):
        mock_service = MagicMock(spec=TaskService)
        mock_task = _make_task_response()
        mock_service.toggle_pin_status.return_value = mock_task

        task_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_tasks_service] = lambda: mock_service
        response = client.patch(f"/api/v1/tasks/{task_id}/unpin")
        assert response.status_code == 200

    async def test_favorite_task_success(self, client, override_deps):
        mock_service = MagicMock(spec=TaskService)
        mock_task = _make_task_response()
        mock_service.toggle_favorite_status.return_value = mock_task

        task_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_tasks_service] = lambda: mock_service
        response = client.patch(f"/api/v1/tasks/{task_id}/favorite")
        assert response.status_code == 200

    async def test_unfavorite_task_success(self, client, override_deps):
        mock_service = MagicMock(spec=TaskService)
        mock_task = _make_task_response()
        mock_service.toggle_favorite_status.return_value = mock_task

        task_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_tasks_service] = lambda: mock_service
        response = client.patch(f"/api/v1/tasks/{task_id}/unfavorite")
        assert response.status_code == 200

    async def test_get_task_history_success(self, client, override_deps):
        mock_service = MagicMock(spec=TaskService)
        mock_service.get_task_history.return_value = []

        task_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_tasks_service] = lambda: mock_service
        response = client.get(f"/api/v1/tasks/{task_id}/history")
        assert response.status_code == 200

    async def test_upload_attachment_success(self, client, override_deps):
        mock_service = AsyncMock(spec=TaskService)
        mock_attachment_service = AsyncMock()
        mock_attachment = MagicMock(spec=AttachmentResponse)
        mock_attachment_service.upload.return_value = mock_attachment

        task_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_tasks_service] = lambda: mock_service
        app.dependency_overrides[get_attachment_service] = lambda: mock_attachment_service
        response = client.post(
            f"/api/v1/tasks/{task_id}/attachments",
            files={"file": ("test.txt", b"hello", "text/plain")},
        )
        assert response.status_code == 201

    async def test_list_attachments_success(self, client, override_deps):
        mock_service = AsyncMock(spec=TaskService)
        mock_attachment_service = AsyncMock()

        task_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_tasks_service] = lambda: mock_service
        app.dependency_overrides[get_attachment_service] = lambda: mock_attachment_service
        response = client.get(f"/api/v1/tasks/{task_id}/attachments")
        assert response.status_code == 200

    async def test_delete_attachment_success(self, client, override_deps):
        mock_service = AsyncMock(spec=TaskService)
        mock_attachment_service = AsyncMock()

        task_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        attachment_id = str(uuid.UUID("87654321-4321-8765-4321-876543218765"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_tasks_service] = lambda: mock_service
        app.dependency_overrides[get_attachment_service] = lambda: mock_attachment_service
        response = client.delete(
            f"/api/v1/tasks/{task_id}/attachments/{attachment_id}"
        )
        assert response.status_code == 200
        assert "success" in response.json()["status"]

    async def test_unauthorized_without_token(self, client, override_deps):
        response = client.get("/api/v1/tasks")
        assert response.status_code == 401
