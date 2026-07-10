import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.core.redis import get_redis_client
from app.modules.ai_suggestions.dependencies import get_current_user_id, get_ai_suggestion_service
from app.modules.tasks.dependencies import get_tasks_service
from app.modules.ai_suggestions.enums import SuggestionStatus
from app.modules.ai_suggestions.exceptions import (
    AISuggestionNotFoundException,
    AISuggestionValidationError,
)
from app.models.meeting_suggested_task import MeetingSuggestedTask


def _uuid(value: str) -> uuid.UUID:
    return uuid.UUID(value)


CURRENT_USER = _uuid("87654321-4321-8765-4321-876543218765")
SUGGESTION_ID = _uuid("12345678-1234-5678-1234-567812345678")
ANALYSIS_ID = _uuid("87654321-4321-8765-4321-876543218765")
TASK_ID = _uuid("11111111-1111-1111-1111-111111111111")


def _make_suggestion(**overrides) -> MeetingSuggestedTask:
    defaults = dict(
        id=SUGGESTION_ID,
        analysis_id=ANALYSIS_ID,
        title="Fix login bug",
        description="OAuth redirect broken",
        priority="HIGH",
        status=SuggestionStatus.PENDING,
        created_task_id=None,
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return MeetingSuggestedTask(**defaults)


def _make_mock_redis():
    mock = AsyncMock()
    mock_pipeline = AsyncMock()
    mock_pipeline.zremrangebyscore = MagicMock()
    mock_pipeline.zcard = MagicMock()
    mock_pipeline.zrange = MagicMock()
    mock_pipeline.zadd = MagicMock()
    mock_pipeline.expire = MagicMock()
    mock_pipeline.execute = AsyncMock(return_value=[0, 0, []])
    mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
    mock_pipeline.__aexit__ = AsyncMock(return_value=False)
    # redis.pipeline is a synchronous call returning an async context manager
    mock.pipeline = MagicMock(return_value=mock_pipeline)
    return mock


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_redis():
    return _make_mock_redis()


@pytest.fixture
def mock_suggestion_service():
    return AsyncMock()


@pytest.fixture
def mock_task_service():
    return MagicMock()


@pytest.fixture
def override_deps(mock_db, mock_redis, mock_suggestion_service, mock_task_service):
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_redis_client] = lambda: mock_redis
    app.dependency_overrides[get_current_user_id] = lambda: CURRENT_USER
    app.dependency_overrides[get_ai_suggestion_service] = lambda: mock_suggestion_service
    app.dependency_overrides[get_tasks_service] = lambda: mock_task_service
    yield
    app.dependency_overrides.clear()


class TestAISuggestionRoutes:
    # ---- create-task --------------------------------------------------
    def test_create_task_success(self, client, override_deps, mock_suggestion_service):
        suggestion = _make_suggestion(status=SuggestionStatus.CREATED, created_task_id=TASK_ID)
        mock_suggestion_service.create_task_from_suggestion.return_value = suggestion
        response = client.post(
            f"/api/v1/ai-suggestions/{SUGGESTION_ID}/create-task",
            json={"title": "Override"},
            headers={"Authorization": "Bearer token"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == str(SUGGESTION_ID)
        assert body["created_task_id"] == str(TASK_ID)
        assert body["status"] == "CREATED"
        # user id propagated (positional arg to the service)
        assert mock_suggestion_service.create_task_from_suggestion.call_args.args[0] == CURRENT_USER

    def test_create_task_not_found(self, client, override_deps, mock_suggestion_service):
        mock_suggestion_service.create_task_from_suggestion.side_effect = AISuggestionNotFoundException(SUGGESTION_ID)
        response = client.post(
            f"/api/v1/ai-suggestions/{SUGGESTION_ID}/create-task",
            json={},
            headers={"Authorization": "Bearer token"},
        )
        assert response.status_code == 404

    def test_create_task_validation_error(self, client, override_deps, mock_suggestion_service):
        mock_suggestion_service.create_task_from_suggestion.side_effect = AISuggestionValidationError("already REJECTED")
        response = client.post(
            f"/api/v1/ai-suggestions/{SUGGESTION_ID}/create-task",
            json={},
            headers={"Authorization": "Bearer token"},
        )
        assert response.status_code == 400

    def test_create_task_requires_auth(self, client, override_deps):
        # Remove the auth override to simulate missing credentials
        app.dependency_overrides.pop(get_current_user_id, None)
        response = client.post(
            f"/api/v1/ai-suggestions/{SUGGESTION_ID}/create-task",
            json={},
        )
        assert response.status_code in (401, 403)
        app.dependency_overrides[get_current_user_id] = lambda: CURRENT_USER

    # ---- reject -------------------------------------------------------
    def test_reject_success(self, client, override_deps, mock_suggestion_service):
        suggestion = _make_suggestion(status=SuggestionStatus.REJECTED)
        mock_suggestion_service.reject_suggestion.return_value = suggestion
        response = client.post(
            f"/api/v1/ai-suggestions/{SUGGESTION_ID}/reject",
            headers={"Authorization": "Bearer token"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "REJECTED"
        # user id propagated (positional arg to the service)
        assert mock_suggestion_service.reject_suggestion.call_args.args[0] == CURRENT_USER

    def test_reject_not_found(self, client, override_deps, mock_suggestion_service):
        mock_suggestion_service.reject_suggestion.side_effect = AISuggestionNotFoundException(SUGGESTION_ID)
        response = client.post(
            f"/api/v1/ai-suggestions/{SUGGESTION_ID}/reject",
            headers={"Authorization": "Bearer token"},
        )
        assert response.status_code == 404

    def test_reject_validation_error(self, client, override_deps, mock_suggestion_service):
        mock_suggestion_service.reject_suggestion.side_effect = AISuggestionValidationError("already CREATED")
        response = client.post(
            f"/api/v1/ai-suggestions/{SUGGESTION_ID}/reject",
            headers={"Authorization": "Bearer token"},
        )
        assert response.status_code == 400

    # ---- list ---------------------------------------------------------
    def test_list_suggestions_success(self, client, override_deps, mock_suggestion_service):
        s1 = _make_suggestion(title="A")
        s2 = _make_suggestion(title="B")
        mock_suggestion_service.list_suggestions.return_value = [s1, s2]
        response = client.get(
            f"/api/v1/ai-suggestions?analysis_id={ANALYSIS_ID}",
            headers={"Authorization": "Bearer token"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total_count"] == 2
        assert len(body["suggestions"]) == 2

    def test_list_suggestions_empty(self, client, override_deps, mock_suggestion_service):
        mock_suggestion_service.list_suggestions.return_value = []
        response = client.get(
            f"/api/v1/ai-suggestions?analysis_id={ANALYSIS_ID}",
            headers={"Authorization": "Bearer token"},
        )
        assert response.status_code == 200
        assert response.json()["total_count"] == 0

    def test_list_suggestions_requires_analysis_id(self, client, override_deps):
        response = client.get(
            "/api/v1/ai-suggestions",
            headers={"Authorization": "Bearer token"},
        )
        assert response.status_code == 422

    def test_list_suggestions_requires_auth(self, client, override_deps):
        app.dependency_overrides.pop(get_current_user_id, None)
        response = client.get(
            f"/api/v1/ai-suggestions?analysis_id={ANALYSIS_ID}",
        )
        assert response.status_code in (401, 403)
        app.dependency_overrides[get_current_user_id] = lambda: CURRENT_USER
