import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from app.modules.attachments.enums import AttachmentEntityType
from app.modules.attachments.exceptions import (
    AttachmentAccessDeniedException,
    AttachmentNotFoundException,
    AttachmentStorageError,
    AttachmentValidationError,
)
from app.modules.attachments.schemas import AttachmentListResponse, AttachmentResponse, PresignedUploadResponse
from app.modules.attachments.service import AttachmentService
from app.modules.attachments.controller import AttachmentController


@pytest.fixture
def mock_service():
    return AsyncMock(spec=AttachmentService)


@pytest.fixture
def controller(mock_service):
    return AttachmentController(mock_service)


def _make_response(**kwargs):
    return AttachmentResponse(
        id=kwargs.get("id", uuid.UUID("12345678-1234-5678-1234-567812345678")),
        owner_user_id=kwargs.get("owner_user_id", uuid.UUID("87654321-4321-8765-4321-876543218765")),
        entity_type=kwargs.get("entity_type", AttachmentEntityType.TASK),
        entity_id=kwargs.get("entity_id", uuid.UUID("12345678-1234-5678-1234-567812345678")),
        original_filename=kwargs.get("original_filename", "report.pdf"),
        stored_filename=kwargs.get("stored_filename", "a1b2_report.pdf"),
        content_type=kwargs.get("content_type", "application/pdf"),
        extension=kwargs.get("extension", "pdf"),
        size=kwargs.get("size", 1024),
        storage_provider=kwargs.get("storage_provider", "local"),
        created_at=kwargs.get("created_at", datetime.now(timezone.utc)),
        updated_at=kwargs.get("updated_at", datetime.now(timezone.utc)),
    )


class TestAttachmentControllerUpload:
    async def test_upload_success(self, controller, mock_service):
        mock_service.upload = AsyncMock(return_value=_make_response())
        result = await controller.upload(uuid.uuid4(), AttachmentEntityType.TASK, uuid.uuid4(), MagicMock())
        assert isinstance(result, AttachmentResponse)
        assert result.extension == "pdf"

    async def test_upload_validation_error_maps_to_422(self, controller, mock_service):
        mock_service.upload = AsyncMock(side_effect=AttachmentValidationError("bad file"))
        with pytest.raises(HTTPException) as exc_info:
            await controller.upload(uuid.uuid4(), AttachmentEntityType.TASK, uuid.uuid4(), MagicMock())
        assert exc_info.value.status_code == 422

    async def test_upload_storage_error_maps_to_500(self, controller, mock_service):
        mock_service.upload = AsyncMock(side_effect=AttachmentStorageError("disk full"))
        with pytest.raises(HTTPException) as exc_info:
            await controller.upload(uuid.uuid4(), AttachmentEntityType.TASK, uuid.uuid4(), MagicMock())
        assert exc_info.value.status_code == 500

    async def test_upload_detail_matches_exception_message(self, controller, mock_service):
        msg = "File too large"
        mock_service.upload = AsyncMock(side_effect=AttachmentValidationError(msg))
        with pytest.raises(HTTPException) as exc_info:
            await controller.upload(uuid.uuid4(), AttachmentEntityType.TASK, uuid.uuid4(), MagicMock())
        assert exc_info.value.detail == msg


class TestAttachmentControllerGetMetadata:
    async def test_get_metadata_success(self, controller, mock_service):
        mock_service.get_metadata = AsyncMock(return_value=_make_response())
        result = await controller.get_metadata(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.uuid4())
        assert isinstance(result, AttachmentResponse)

    async def test_get_metadata_not_found_maps_to_404(self, controller, mock_service):
        mock_service.get_metadata = AsyncMock(side_effect=AttachmentNotFoundException(uuid.UUID("12345678-1234-5678-1234-567812345678")))
        with pytest.raises(HTTPException) as exc_info:
            await controller.get_metadata(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.uuid4())
        assert exc_info.value.status_code == 404

    async def test_get_metadata_access_denied_maps_to_403(self, controller, mock_service):
        mock_service.get_metadata = AsyncMock(side_effect=AttachmentAccessDeniedException(uuid.UUID("12345678-1234-5678-1234-567812345678")))
        with pytest.raises(HTTPException) as exc_info:
            await controller.get_metadata(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.uuid4())
        assert exc_info.value.status_code == 403


class TestAttachmentControllerDownload:
    async def test_download_success_returns_file_response(self, controller, mock_service):
        mock_service.get_download_response = AsyncMock(return_value={
            "url": None,
            "path": "/attachments/report.pdf",
            "content_type": "application/pdf",
            "original_filename": "report.pdf",
        })
        result = await controller.download(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.uuid4())
        assert isinstance(result, FileResponse)

    async def test_download_success_returns_redirect(self, controller, mock_service):
        mock_service.get_download_response = AsyncMock(return_value={
            "url": "https://s3.amazonaws.com/bucket/key",
            "path": None,
            "content_type": "application/pdf",
            "original_filename": "report.pdf",
        })
        result = await controller.download(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.uuid4())
        assert isinstance(result, RedirectResponse)

    async def test_download_not_found_maps_to_404(self, controller, mock_service):
        mock_service.get_download_response = AsyncMock(side_effect=AttachmentNotFoundException(uuid.UUID("12345678-1234-5678-1234-567812345678")))
        with pytest.raises(HTTPException) as exc_info:
            await controller.download(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.uuid4())
        assert exc_info.value.status_code == 404

    async def test_download_access_denied_maps_to_403(self, controller, mock_service):
        mock_service.get_download_response = AsyncMock(side_effect=AttachmentAccessDeniedException(uuid.UUID("12345678-1234-5678-1234-567812345678")))
        with pytest.raises(HTTPException) as exc_info:
            await controller.download(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.uuid4())
        assert exc_info.value.status_code == 403


class TestAttachmentControllerPresigned:
    async def test_create_presigned_upload_success(self, controller, mock_service):
        mock_service.create_presigned_upload = AsyncMock(return_value={
            "upload_url": "https://s3/presigned",
            "key": "tasks/123/a1b2_report.pdf",
            "expires_in": 3600,
        })
        result = await controller.create_presigned_upload(
            owner_user_id=uuid.uuid4(),
            entity_type=AttachmentEntityType.TASK,
            entity_id=uuid.uuid4(),
            filename="report.pdf",
            content_type="application/pdf",
        )
        assert isinstance(result, PresignedUploadResponse)
        assert result.expires_in == 3600

    async def test_create_presigned_upload_storage_error_maps_to_500(self, controller, mock_service):
        mock_service.create_presigned_upload = AsyncMock(side_effect=AttachmentStorageError("provider error"))
        with pytest.raises(HTTPException) as exc_info:
            await controller.create_presigned_upload(
                owner_user_id=uuid.uuid4(),
                entity_type=AttachmentEntityType.TASK,
                entity_id=uuid.uuid4(),
                filename="report.pdf",
                content_type="application/pdf",
            )
        assert exc_info.value.status_code == 500


class TestAttachmentControllerConfirmPresigned:
    async def test_confirm_presigned_upload_success(self, controller, mock_service):
        mock_service.confirm_presigned_upload = AsyncMock(return_value=_make_response())
        result = await controller.confirm_presigned_upload(
            owner_user_id=uuid.uuid4(),
            entity_type=AttachmentEntityType.TASK,
            entity_id=uuid.uuid4(),
            key="tasks/123/a1b2_report.pdf",
            original_filename="report.pdf",
            content_type="application/pdf",
            size=1024,
        )
        assert isinstance(result, AttachmentResponse)

    async def test_confirm_presigned_upload_storage_error_maps_to_500(self, controller, mock_service):
        mock_service.confirm_presigned_upload = AsyncMock(side_effect=AttachmentStorageError("provider error"))
        with pytest.raises(HTTPException) as exc_info:
            await controller.confirm_presigned_upload(
                owner_user_id=uuid.uuid4(),
                entity_type=AttachmentEntityType.TASK,
                entity_id=uuid.uuid4(),
                key="tasks/123/a1b2_report.pdf",
                original_filename="report.pdf",
                content_type="application/pdf",
                size=1024,
            )
        assert exc_info.value.status_code == 500


class TestAttachmentControllerList:
    async def test_list_for_entity_success(self, controller, mock_service):
        mock_service.list_for_entity = AsyncMock(return_value=[_make_response()])
        result = await controller.list_for_entity(AttachmentEntityType.TASK, uuid.uuid4(), uuid.uuid4())
        assert isinstance(result, AttachmentListResponse)
        assert result.total_count == 1

    async def test_list_for_entity_access_denied_maps_to_403(self, controller, mock_service):
        mock_service.list_for_entity = AsyncMock(side_effect=AttachmentAccessDeniedException(uuid.UUID("12345678-1234-5678-1234-567812345678")))
        with pytest.raises(HTTPException) as exc_info:
            await controller.list_for_entity(AttachmentEntityType.TASK, uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == 403

    async def test_list_recent_success(self, controller, mock_service):
        mock_service.list_recent_for_user = AsyncMock(return_value=[_make_response()])
        result = await controller.list_recent(uuid.uuid4(), limit=10)
        assert isinstance(result, AttachmentListResponse)
        assert result.total_count == 1


class TestAttachmentControllerDelete:
    async def test_delete_success(self, controller, mock_service):
        mock_service.delete = AsyncMock()
        result = await controller.delete(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.uuid4())
        assert result["status"] == "success"
        assert "deleted" in result["message"].lower()

    async def test_delete_not_found_maps_to_404(self, controller, mock_service):
        mock_service.delete = AsyncMock(side_effect=AttachmentNotFoundException(uuid.UUID("12345678-1234-5678-1234-567812345678")))
        with pytest.raises(HTTPException) as exc_info:
            await controller.delete(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.uuid4())
        assert exc_info.value.status_code == 404

    async def test_delete_access_denied_maps_to_403(self, controller, mock_service):
        mock_service.delete = AsyncMock(side_effect=AttachmentAccessDeniedException(uuid.UUID("12345678-1234-5678-1234-567812345678")))
        with pytest.raises(HTTPException) as exc_info:
            await controller.delete(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.uuid4())
        assert exc_info.value.status_code == 403
