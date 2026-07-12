import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.main import app
from app.core.database import get_db
from app.core.redis import get_redis_client
from app.modules.meetings.dependencies import get_current_user_id
from app.modules.whiteboard.controller import WhiteboardController
from app.modules.whiteboard.service import WhiteboardService
from app.modules.whiteboard.schemas import (
    WhiteboardCreate,
    WhiteboardRename,
    WhiteboardAutosave,
    WhiteboardResponse,
    WhiteboardFilters,
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


def _make_board_response(**kwargs):
    now = datetime.now(timezone.utc)
    return WhiteboardResponse(
        id=kwargs.get("id", uuid.UUID("12345678-1234-5678-1234-567812345678")),
        user_id=kwargs.get("user_id", uuid.UUID("87654321-4321-8765-4321-876543218765")),
        title=kwargs.get("title", "Test Board"),
        board_data=kwargs.get("board_data", {"version": 1, "elements": []}),
        is_favorite=kwargs.get("is_favorite", False),
        is_archived=kwargs.get("is_archived", False),
        is_deleted=kwargs.get("is_deleted", False),
        created_at=now,
        updated_at=now,
        deleted_at=kwargs.get("deleted_at", None),
    )


class TestWhiteboardRoutes:
    async def test_create_board_success(self, client, override_deps):
        mock_service = MagicMock(spec=WhiteboardService)
        mock_board = _make_board_response()
        mock_service.create_board.return_value = mock_board

        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        from app.modules.whiteboard.routes import get_whiteboard_service
        app.dependency_overrides[get_whiteboard_service] = lambda: mock_service
        response = client.post(
            "/api/v1/whiteboards",
            json={"title": "New Board"},
        )
        assert response.status_code == 201
        assert response.json()["title"] == "Test Board"

    async def test_create_board_empty_title_raises(self, client, override_deps):
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        from app.modules.whiteboard.routes import get_whiteboard_service
        app.dependency_overrides[get_whiteboard_service] = lambda: MagicMock()
        response = client.post(
            "/api/v1/whiteboards",
            json={"title": "   "},
        )
        assert response.status_code == 422

    async def test_list_boards_success(self, client, override_deps):
        mock_service = MagicMock(spec=WhiteboardService)
        mock_service.list_user_boards.return_value = [_make_board_response()]

        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        from app.modules.whiteboard.routes import get_whiteboard_service
        app.dependency_overrides[get_whiteboard_service] = lambda: mock_service
        response = client.get("/api/v1/whiteboards")
        assert response.status_code == 200
        assert len(response.json()) == 1

    async def test_list_boards_with_filters(self, client, override_deps):
        mock_service = MagicMock(spec=WhiteboardService)
        mock_service.list_user_boards.return_value = []

        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        from app.modules.whiteboard.routes import get_whiteboard_service
        app.dependency_overrides[get_whiteboard_service] = lambda: mock_service
        response = client.get(
            "/api/v1/whiteboards",
            params={
                "is_archived": "false",
                "is_deleted": "false",
                "is_favorite": "true",
                "search": "meeting",
            },
        )
        assert response.status_code == 200

    async def test_get_board_success(self, client, override_deps):
        mock_service = MagicMock(spec=WhiteboardService)
        mock_board = _make_board_response()
        mock_service.get_board.return_value = mock_board

        board_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        from app.modules.whiteboard.routes import get_whiteboard_service
        app.dependency_overrides[get_whiteboard_service] = lambda: mock_service
        response = client.get(f"/api/v1/whiteboards/{board_id}")
        assert response.status_code == 200
        assert response.json()["id"] == board_id

    async def test_get_board_access_denied(self, client, override_deps):
        from app.modules.whiteboard.exceptions import WhiteboardAccessDeniedException
        mock_service = MagicMock(spec=WhiteboardService)
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_service.get_board.side_effect = WhiteboardAccessDeniedException(board_id, uuid.UUID("87654321-4321-8765-4321-876543218765"))

        board_id = str(board_id)
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        from app.modules.whiteboard.routes import get_whiteboard_service
        app.dependency_overrides[get_whiteboard_service] = lambda: mock_service
        response = client.get(f"/api/v1/whiteboards/{board_id}")
        assert response.status_code == 403

    async def test_rename_board_success(self, client, override_deps):
        mock_service = MagicMock(spec=WhiteboardService)
        mock_board = _make_board_response(title="Renamed")
        mock_service.rename_board.return_value = mock_board

        board_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        from app.modules.whiteboard.routes import get_whiteboard_service
        app.dependency_overrides[get_whiteboard_service] = lambda: mock_service
        response = client.patch(
            f"/api/v1/whiteboards/{board_id}",
            json={"title": "Renamed"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Renamed"

    async def test_autosave_board_success(self, client, override_deps):
        mock_service = MagicMock(spec=WhiteboardService)
        mock_board = _make_board_response()
        mock_service.update_board_payload.return_value = mock_board

        board_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        from app.modules.whiteboard.routes import get_whiteboard_service
        app.dependency_overrides[get_whiteboard_service] = lambda: mock_service
        response = client.patch(
            f"/api/v1/whiteboards/{board_id}/board",
            json={"board_data": {"version": 2, "elements": []}},
        )
        assert response.status_code == 200

    async def test_toggle_favorite_success(self, client, override_deps):
        mock_service = MagicMock(spec=WhiteboardService)
        mock_board = _make_board_response()
        mock_service.toggle_favorite.return_value = mock_board

        board_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        from app.modules.whiteboard.routes import get_whiteboard_service
        app.dependency_overrides[get_whiteboard_service] = lambda: mock_service
        response = client.patch(f"/api/v1/whiteboards/{board_id}/favorite?is_favorite=true")
        assert response.status_code == 200

    async def test_toggle_archive_success(self, client, override_deps):
        mock_service = MagicMock(spec=WhiteboardService)
        mock_board = _make_board_response(is_archived=True)
        mock_service.toggle_archive.return_value = mock_board

        board_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        from app.modules.whiteboard.routes import get_whiteboard_service
        app.dependency_overrides[get_whiteboard_service] = lambda: mock_service
        response = client.patch(f"/api/v1/whiteboards/{board_id}/archive?is_archived=true")
        assert response.status_code == 200

    async def test_delete_board_success(self, client, override_deps):
        mock_service = MagicMock(spec=WhiteboardService)
        mock_service.soft_delete_board.return_value = None

        board_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        from app.modules.whiteboard.routes import get_whiteboard_service
        app.dependency_overrides[get_whiteboard_service] = lambda: mock_service
        response = client.delete(f"/api/v1/whiteboards/{board_id}")
        assert response.status_code == 200
        assert "soft-deleted" in response.json()["message"]

    async def test_restore_board_success(self, client, override_deps):
        mock_service = MagicMock(spec=WhiteboardService)
        mock_board = _make_board_response()
        mock_service.restore_board.return_value = mock_board

        board_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("87654321-4321-8765-4321-876543218765")
        from app.modules.whiteboard.routes import get_whiteboard_service
        app.dependency_overrides[get_whiteboard_service] = lambda: mock_service
        response = client.patch(f"/api/v1/whiteboards/{board_id}/restore")
        assert response.status_code == 200
        assert response.json()["id"] == board_id

    async def test_unauthorized_without_token(self, client, override_deps):
        response = client.get("/api/v1/whiteboards")
        assert response.status_code == 401
