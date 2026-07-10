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
from app.modules.notes.dependencies import get_current_user_id, get_notes_service
from app.modules.notes.controller import NoteController
from app.modules.notes.services import NoteService
from app.modules.notes.schemas import (
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    NoteListResponse,
)


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


def _make_note_response(**kwargs):
    now = datetime.now(timezone.utc)
    return NoteResponse(
        id=kwargs.get("id", uuid.UUID("12345678-1234-5678-1234-567812345678")),
        user_id=kwargs.get("user_id", uuid.UUID("87654321-4321-8765-4321-876543218765")),
        title=kwargs.get("title", "Test Note"),
        content=kwargs.get("content", "Content"),
        category=kwargs.get("category", "personal"),
        tags=kwargs.get("tags", []),
        is_pinned=kwargs.get("is_pinned", False),
        is_favorite=kwargs.get("is_favorite", False),
        is_archived=kwargs.get("is_archived", False),
        created_at=now,
        updated_at=now,
        deleted_at=kwargs.get("deleted_at", None),
    )


class TestNotesRoutes:
    async def test_create_note_success(self, client, override_deps):
        mock_service = AsyncMock(spec=NoteService)
        mock_note = _make_note_response()
        mock_service.create_note.return_value = mock_note

        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_notes_service] = lambda: mock_service
        response = client.post(
            "/api/v1/notes",
            json={"title": "New Note", "content": "Content"},
        )
        assert response.status_code == 201
        assert response.json()["title"] == "Test Note"

    async def test_create_note_empty_content_raises(self, client, override_deps):
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_notes_service] = lambda: MagicMock()
        response = client.post(
            "/api/v1/notes",
            json={"title": "   ", "content": "   "},
        )
        assert response.status_code == 422

    async def test_list_notes_success(self, client, override_deps):
        mock_service = AsyncMock(spec=NoteService)
        mock_service.list_and_filter_notes.return_value = [_make_note_response()]

        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_notes_service] = lambda: mock_service
        response = client.get("/api/v1/notes")
        assert response.status_code == 200
        assert response.json()["total_count"] == 1

    async def test_list_notes_with_filters(self, client, override_deps):
        mock_service = AsyncMock(spec=NoteService)
        mock_service.list_and_filter_notes.return_value = []

        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_notes_service] = lambda: mock_service
        response = client.get(
            "/api/v1/notes",
            params={
                "search": "meeting",
                "category": "work",
                "tag": "urgent",
                "favorite": "true",
                "pinned": "false",
                "archived": "false",
                "deleted": "false",
                "sort_by": "created_at",
                "sort_order": "asc",
            },
        )
        assert response.status_code == 200

    async def test_get_analytics_success(self, client, override_deps):
        mock_service = AsyncMock(spec=NoteService)
        mock_service.get_analytics.return_value = {"total": 5, "favorite": 2}

        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_notes_service] = lambda: mock_service
        response = client.get("/api/v1/notes/analytics")
        assert response.status_code == 200
        assert response.json()["total"] == 5

    async def test_get_note_success(self, client, override_deps):
        mock_service = AsyncMock(spec=NoteService)
        mock_note = _make_note_response()
        mock_service.get_note.return_value = mock_note

        note_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_notes_service] = lambda: mock_service
        response = client.get(f"/api/v1/notes/{note_id}")
        assert response.status_code == 200
        assert response.json()["id"] == note_id

    async def test_get_note_access_denied(self, client, override_deps):
        mock_service = AsyncMock(spec=NoteService)
        from app.modules.notes.exceptions import NoteAccessDeniedException
        mock_service.get_note.side_effect = NoteAccessDeniedException(
            uuid.UUID("12345678-1234-5678-1234-567812345678"),
            uuid.UUID("87654321-4321-8765-4321-876543218765"),
        )

        note_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_notes_service] = lambda: mock_service
        response = client.get(f"/api/v1/notes/{note_id}")
        assert response.status_code == 403

    async def test_update_note_success(self, client, override_deps):
        mock_service = AsyncMock(spec=NoteService)
        mock_note = _make_note_response(title="Updated")
        mock_service.update_note.return_value = mock_note

        note_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_notes_service] = lambda: mock_service
        response = client.patch(
            f"/api/v1/notes/{note_id}",
            json={"title": "Updated"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated"

    async def test_delete_note_success(self, client, override_deps):
        mock_service = AsyncMock(spec=NoteService)
        mock_service.delete_note.return_value = None

        note_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_notes_service] = lambda: mock_service
        response = client.delete(f"/api/v1/notes/{note_id}")
        assert response.status_code == 200
        assert "trash" in response.json()["message"]

    async def test_restore_note_success(self, client, override_deps):
        mock_service = AsyncMock(spec=NoteService)
        mock_note = _make_note_response()
        mock_service.restore_note.return_value = mock_note

        note_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_notes_service] = lambda: mock_service
        response = client.patch(f"/api/v1/notes/{note_id}/restore")
        assert response.status_code == 200
        assert response.json()["id"] == note_id

    async def test_archive_note_success(self, client, override_deps):
        mock_service = AsyncMock(spec=NoteService)
        mock_note = _make_note_response()
        mock_service.toggle_archive_status.return_value = mock_note

        note_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_notes_service] = lambda: mock_service
        response = client.patch(f"/api/v1/notes/{note_id}/archive")
        assert response.status_code == 200

    async def test_unarchive_note_success(self, client, override_deps):
        mock_service = AsyncMock(spec=NoteService)
        mock_note = _make_note_response()
        mock_service.toggle_archive_status.return_value = mock_note

        note_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_notes_service] = lambda: mock_service
        response = client.patch(f"/api/v1/notes/{note_id}/unarchive")
        assert response.status_code == 200

    async def test_pin_note_success(self, client, override_deps):
        mock_service = AsyncMock(spec=NoteService)
        mock_note = _make_note_response()
        mock_service.toggle_pin_status.return_value = mock_note

        note_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_notes_service] = lambda: mock_service
        response = client.patch(f"/api/v1/notes/{note_id}/pin")
        assert response.status_code == 200

    async def test_unpin_note_success(self, client, override_deps):
        mock_service = AsyncMock(spec=NoteService)
        mock_note = _make_note_response()
        mock_service.toggle_pin_status.return_value = mock_note

        note_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_notes_service] = lambda: mock_service
        response = client.patch(f"/api/v1/notes/{note_id}/unpin")
        assert response.status_code == 200

    async def test_favorite_note_success(self, client, override_deps):
        mock_service = AsyncMock(spec=NoteService)
        mock_note = _make_note_response()
        mock_service.toggle_favorite_status.return_value = mock_note

        note_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_notes_service] = lambda: mock_service
        response = client.patch(f"/api/v1/notes/{note_id}/favorite")
        assert response.status_code == 200

    async def test_unfavorite_note_success(self, client, override_deps):
        mock_service = AsyncMock(spec=NoteService)
        mock_note = _make_note_response()
        mock_service.toggle_favorite_status.return_value = mock_note

        note_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        app.dependency_overrides[get_notes_service] = lambda: mock_service
        response = client.patch(f"/api/v1/notes/{note_id}/unfavorite")
        assert response.status_code == 200

    async def test_unauthorized_without_token(self, client, override_deps):
        response = client.get("/api/v1/notes")
        assert response.status_code == 401
