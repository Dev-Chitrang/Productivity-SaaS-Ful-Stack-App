import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.database import get_db
from app.core.redis import get_redis_client
from app.modules.attachments.routes import router as attachments_router
from app.modules.attachments.dependencies import get_attachment_service, get_current_user_id
from app.modules.attachments.controller import AttachmentController
from app.modules.attachments.schemas import AttachmentListResponse, AttachmentResponse, PresignedUploadResponse

# Build a dedicated test application that includes the attachments router.
# (The attachments router is not registered in app.main, so we create our own.)
test_app = FastAPI()
test_app.include_router(attachments_router, prefix="/api/v1")


@pytest.fixture
def client():
    return TestClient(test_app)


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

    test_app.dependency_overrides[get_db] = _get_db
    test_app.dependency_overrides[get_redis_client] = _get_redis
    yield
    test_app.dependency_overrides.clear()


def _make_attachment_response(**kwargs):
    now = datetime.now(timezone.utc)
    return AttachmentResponse(
        id=kwargs.get("id", uuid.UUID("12345678-1234-5678-1234-567812345678")),
        owner_user_id=kwargs.get("owner_user_id", uuid.UUID("87654321-4321-8765-4321-876543218765")),
        entity_type=kwargs.get("entity_type", "TASK"),
        entity_id=kwargs.get("entity_id", uuid.UUID("12345678-1234-5678-1234-567812345678")),
        original_filename=kwargs.get("original_filename", "report.pdf"),
        stored_filename=kwargs.get("stored_filename", "a1b2_report.pdf"),
        content_type=kwargs.get("content_type", "application/pdf"),
        extension=kwargs.get("extension", "pdf"),
        size=kwargs.get("size", 1024),
        storage_provider=kwargs.get("storage_provider", "local"),
        created_at=now,
        updated_at=now,
    )


class TestAttachmentRoutes:
    async def test_upload_attachment_success(self, client, override_deps):
        mock_service = AsyncMock(spec=AttachmentController)
        mock_service.upload.return_value = _make_attachment_response()

        test_app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("12345678-1234-5678-1234-567812345678")
        test_app.dependency_overrides[get_attachment_service] = lambda: mock_service
        response = client.post(
            "/api/v1/attachments",
            data={"entity_type": "TASK", "entity_id": str(uuid.UUID("12345678-1234-5678-1234-567812345678"))},
            files={"file": ("report.pdf", b"%PDF-1.4 fake pdf content", "application/pdf")},
            headers={"Authorization": "Bearer dummy-token"},
        )
        assert response.status_code == 201
        assert response.json()["extension"] == "pdf"

    async def test_create_presigned_upload_success(self, client, override_deps):
        mock_service = AsyncMock()
        mock_service.create_presigned_upload.return_value = {
            "upload_url": "https://s3.amazonaws.com/bucket/key",
            "key": "tasks/123/a1b2_report.pdf",
            "expires_in": 3600,
        }

        test_app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("12345678-1234-5678-1234-567812345678")
        test_app.dependency_overrides[get_attachment_service] = lambda: mock_service
        response = client.post(
            "/api/v1/attachments/presigned-upload",
            json={
                "entity_type": "TASK",
                "entity_id": str(uuid.UUID("12345678-1234-5678-1234-567812345678")),
                "filename": "report.pdf",
                "content_type": "application/pdf",
            },
            headers={"Authorization": "Bearer dummy-token"},
        )
        assert response.status_code == 200
        assert response.json()["expires_in"] == 3600

    async def test_confirm_presigned_upload_success(self, client, override_deps):
        mock_service = AsyncMock()
        mock_service.confirm_presigned_upload.return_value = _make_attachment_response()

        test_app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("12345678-1234-5678-1234-567812345678")
        test_app.dependency_overrides[get_attachment_service] = lambda: mock_service
        response = client.post(
            "/api/v1/attachments/confirm-upload",
            json={
                "entity_type": "TASK",
                "entity_id": str(uuid.UUID("12345678-1234-5678-1234-567812345678")),
                "key": "tasks/123/a1b2_report.pdf",
                "original_filename": "report.pdf",
                "content_type": "application/pdf",
                "size": 1024,
            },
            headers={"Authorization": "Bearer dummy-token"},
        )
        assert response.status_code == 201

    async def test_list_recent_attachments_success(self, client, override_deps):
        mock_service = AsyncMock()
        mock_service.list_recent_for_user.return_value = [_make_attachment_response()]

        test_app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("12345678-1234-5678-1234-567812345678")
        test_app.dependency_overrides[get_attachment_service] = lambda: mock_service
        response = client.get("/api/v1/attachments/recent", headers={"Authorization": "Bearer dummy-token"})
        assert response.status_code == 200
        assert response.json()["total_count"] == 1

    async def test_list_recent_attachments_with_limit(self, client, override_deps):
        mock_service = AsyncMock()
        mock_service.list_recent_for_user.return_value = []

        test_app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("12345678-1234-5678-1234-567812345678")
        test_app.dependency_overrides[get_attachment_service] = lambda: mock_service
        response = client.get("/api/v1/attachments/recent?limit=5", headers={"Authorization": "Bearer dummy-token"})
        assert response.status_code == 200

    async def test_get_attachment_metadata_success(self, client, override_deps):
        mock_service = AsyncMock()
        mock_service.get_metadata.return_value = _make_attachment_response()
        attachment_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))

        test_app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("12345678-1234-5678-1234-567812345678")
        test_app.dependency_overrides[get_attachment_service] = lambda: mock_service
        response = client.get(f"/api/v1/attachments/{attachment_id}", headers={"Authorization": "Bearer dummy-token"})
        assert response.status_code == 200
        assert response.json()["id"] == attachment_id

    async def test_list_entity_attachments_success(self, client, override_deps):
        mock_service = AsyncMock()
        mock_service.list_for_entity.return_value = [_make_attachment_response()]
        entity_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))

        test_app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("12345678-1234-5678-1234-567812345678")
        test_app.dependency_overrides[get_attachment_service] = lambda: mock_service
        response = client.get(
            "/api/v1/attachments",
            params={"entity_type": "TASK", "entity_id": entity_id},
            headers={"Authorization": "Bearer dummy-token"},
        )
        assert response.status_code == 200
        assert response.json()["total_count"] == 1

    async def test_list_entity_attachments_without_entity_id_returns_422(self, client, override_deps):
        test_app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("12345678-1234-5678-1234-567812345678")
        response = client.get("/api/v1/attachments", params={"entity_type": "TASK"})
        assert response.status_code == 422

    async def test_delete_attachment_success(self, client, override_deps):
        mock_service = AsyncMock()
        attachment_id = str(uuid.UUID("12345678-1234-5678-1234-567812345678"))

        test_app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID("12345678-1234-5678-1234-567812345678")
        test_app.dependency_overrides[get_attachment_service] = lambda: mock_service
        response = client.delete(f"/api/v1/attachments/{attachment_id}")
        assert response.status_code == 200
        assert "success" in response.json()["status"]

    async def test_unauthorized_without_token(self, client, override_deps):
        response = client.get("/api/v1/attachments/recent")
        # FastAPI 0.138+ HTTPBearer returns 401 (was 403 in older versions)
        assert response.status_code == 401
