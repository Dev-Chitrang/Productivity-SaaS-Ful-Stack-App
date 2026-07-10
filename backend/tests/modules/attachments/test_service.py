import uuid
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import UploadFile
from app.modules.attachments.enums import AttachmentEntityType, ENTITY_STORAGE_DIRS
from app.modules.attachments.exceptions import (
    AttachmentAccessDeniedException,
    AttachmentNotFoundException,
    AttachmentStorageError,
    AttachmentValidationError,
)
from app.modules.attachments.service import AttachmentService, _sanitise_filename, _extract_extension


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def mock_storage():
    return AsyncMock()


@pytest.fixture
def service(mock_repo, mock_storage):
    mock_storage.provider_name = "local"
    return AttachmentService(mock_repo, mock_storage)


@pytest.fixture
def sample_attachment():
    from app.models.attachment import Attachment
    return Attachment(
        id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        owner_user_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
        entity_type=AttachmentEntityType.TASK,
        entity_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        original_filename="report.pdf",
        stored_filename="a1b2_report.pdf",
        content_type="application/pdf",
        extension="pdf",
        size=1024,
        storage_provider="local",
        storage_path="/attachments/tasks/123/report.pdf",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def _make_attachment(**kwargs):
    return MagicMock(
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
        storage_path=kwargs.get("storage_path", "/attachments/tasks/123/report.pdf"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestSanitiseFilename:
    def test_normal_filename(self):
        assert _sanitise_filename("report.pdf") == "report.pdf"

    def test_strips_control_chars(self):
        result = _sanitise_filename("file\x00name.pdf")
        assert "\x00" not in result
        assert result in {"filename.pdf", "file_name.pdf"}

    def test_collapses_whitespace_to_underscore(self):
        assert "_" in _sanitise_filename("my  file   name.pdf")

    def test_strips_leading_dots(self):
        assert not _sanitise_filename(".hidden.pdf").startswith(".")
        assert not _sanitise_filename("..hidden.pdf").startswith(".")

    def test_truncates_to_max_length(self):
        long_name = "a" * 300 + ".pdf"
        result = _sanitise_filename(long_name)
        assert len(result) <= 255

    def test_empty_input_falls_back(self):
        assert _sanitise_filename("") == "attachment"

    def test_unsafe_chars_removed(self):
        result = _sanitise_filename("file<name>.pdf")
        assert "<" not in result
        assert ">" not in result

    def test_unicode_normalised(self):
        result = _sanitise_filename("café.pdf")
        assert "é" in result or "e" in result


class TestExtractExtension:
    def test_simple_extension(self):
        assert _extract_extension("file.pdf") == "pdf"

    def test_uppercase_extension(self):
        assert _extract_extension("file.PDF") == "pdf"

    def test_multiple_dots(self):
        assert _extract_extension("my.file.tar.gz") == "gz"

    def test_no_extension(self):
        assert _extract_extension("filename") == ""

    def test_hidden_file(self):
        assert _extract_extension(".gitignore") == ""

    def test_leading_dot_stripped(self):
        assert _extract_extension("file .pdf") == "pdf"


class TestAttachmentServiceUpload:
    async def test_upload_success(self, service, mock_repo, mock_storage):
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "report.pdf"
        mock_file.read = AsyncMock(return_value=b"pdf content")
        mock_storage.save_attachment = AsyncMock(return_value={
            "stored_filename": "a1b2_report.pdf",
            "content_type": "application/pdf",
            "storage_path": "/attachments/tasks/123/a1b2_report.pdf",
            "size": 10,
        })
        mock_repo.stored_filename_exists.return_value = False
        mock_repo.create = AsyncMock(return_value=_make_attachment())

        result = await service.upload(
            owner_user_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            entity_type=AttachmentEntityType.TASK,
            entity_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            file=mock_file,
        )
        assert result is not None
        mock_storage.save_attachment.assert_called_once()
        mock_repo.create.assert_called_once()

    async def test_upload_empty_filename_raises(self, service):
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "   "
        mock_file.read = AsyncMock(return_value=b"content")
        with pytest.raises(AttachmentValidationError, match="filename is required"):
            await service.upload(
                owner_user_id=uuid.uuid4(),
                entity_type=AttachmentEntityType.TASK,
                entity_id=uuid.uuid4(),
                file=mock_file,
            )

    async def test_upload_no_extension_raises(self, service):
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "README"
        mock_file.read = AsyncMock(return_value=b"content")
        with pytest.raises(AttachmentValidationError, match="recognisable extension"):
            await service.upload(
                owner_user_id=uuid.uuid4(),
                entity_type=AttachmentEntityType.TASK,
                entity_id=uuid.uuid4(),
                file=mock_file,
            )

    async def test_upload_storage_validation_propagates(self, service, mock_storage):
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "report.pdf"
        mock_file.read = AsyncMock(return_value=b"pdf content")
        mock_storage.save_attachment = AsyncMock(side_effect=AttachmentValidationError("too large"))
        with pytest.raises(AttachmentValidationError):
            await service.upload(
                owner_user_id=uuid.uuid4(),
                entity_type=AttachmentEntityType.TASK,
                entity_id=uuid.uuid4(),
                file=mock_file,
            )

    async def test_upload_storage_exception_wrapped(self, service, mock_storage):
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "report.pdf"
        mock_file.read = AsyncMock(return_value=b"pdf content")
        mock_storage.save_attachment = AsyncMock(side_effect=Exception("disk full"))
        with pytest.raises(AttachmentStorageError, match="Failed to persist"):
            await service.upload(
                owner_user_id=uuid.uuid4(),
                entity_type=AttachmentEntityType.TASK,
                entity_id=uuid.uuid4(),
                file=mock_file,
            )

    async def test_upload_retries_on_stored_filename_collision(self, service, mock_repo, mock_storage):
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "report.pdf"
        mock_file.read = AsyncMock(return_value=b"pdf content")
        mock_storage.save_attachment = AsyncMock(side_effect=[
            {"stored_filename": "dup_report.pdf", "content_type": "application/pdf", "storage_path": "/p1", "size": 10},
            {"stored_filename": "a1b2_report.pdf", "content_type": "application/pdf", "storage_path": "/p2", "size": 10},
        ])
        mock_repo.stored_filename_exists = AsyncMock(side_effect=[True, False])
        mock_repo.create = AsyncMock(return_value=_make_attachment(stored_filename="a1b2_report.pdf"))
        result = await service.upload(
            owner_user_id=uuid.uuid4(),
            entity_type=AttachmentEntityType.TASK,
            entity_id=uuid.uuid4(),
            file=mock_file,
        )
        assert result.stored_filename == "a1b2_report.pdf"
        assert mock_storage.save_attachment.call_count == 2

    async def test_upload_retry_storage_error_propagates(self, service, mock_repo, mock_storage):
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "report.pdf"
        mock_file.read = AsyncMock(return_value=b"pdf content")
        mock_storage.save_attachment = AsyncMock(side_effect=[
            {"stored_filename": "dup.pdf", "content_type": "application/pdf", "storage_path": "/p1", "size": 10},
            Exception("retry failed"),
        ])
        mock_repo.stored_filename_exists = AsyncMock(side_effect=[True, False])
        with pytest.raises(AttachmentStorageError, match="Storage collision retry failed"):
            await service.upload(
                owner_user_id=uuid.uuid4(),
                entity_type=AttachmentEntityType.TASK,
                entity_id=uuid.uuid4(),
                file=mock_file,
            )


class TestAttachmentServicePresigned:
    async def test_create_presigned_upload_success(self, service, mock_storage):
        mock_storage.create_upload = AsyncMock(return_value={
            "upload_url": "https://s3/presigned",
            "key": "tasks/123/a1b2_report.pdf",
            "expires_in": 3600,
        })
        result = await service.create_presigned_upload(
            owner_user_id=uuid.uuid4(),
            entity_type=AttachmentEntityType.TASK,
            entity_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            filename="report.pdf",
            content_type="application/pdf",
        )
        assert result["upload_url"] == "https://s3/presigned"
        assert result["expires_in"] == 3600
        assert "tasks" in result["key"]

    async def test_create_presigned_upload_no_extension_raises(self, service):
        with pytest.raises(AttachmentValidationError, match="recognisable extension"):
            await service.create_presigned_upload(
                owner_user_id=uuid.uuid4(),
                entity_type=AttachmentEntityType.TASK,
                entity_id=uuid.uuid4(),
                filename="README",
                content_type="application/pdf",
            )


class TestAttachmentServiceConfirmPresigned:
    async def test_confirm_presigned_upload_success(self, service, mock_storage, mock_repo):
        mock_storage.confirm_upload = AsyncMock(return_value={
            "storage_path": "tasks/123/a1b2_report.pdf",
            "size": 1024,
        })
        mock_repo.create = AsyncMock(return_value=_make_attachment(stored_filename="a1b2_report.pdf"))
        result = await service.confirm_presigned_upload(
            owner_user_id=uuid.uuid4(),
            entity_type=AttachmentEntityType.TASK,
            entity_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            key="tasks/123/a1b2_report.pdf",
            original_filename="report.pdf",
            content_type="application/pdf",
            size=1024,
        )
        assert result is not None
        mock_repo.create.assert_called_once()


class TestAttachmentServiceDownload:
    async def test_get_download_response_success(self, service, mock_repo, mock_storage):
        attachment = _make_attachment(storage_path="/attachments/tasks/123/report.pdf")
        mock_repo.get_by_id = AsyncMock(return_value=attachment)
        mock_storage.exists = MagicMock(return_value=True)
        mock_storage.get_download_response = AsyncMock(return_value={"url": None, "path": "/local/path"})
        result = await service.get_download_response(attachment.id, attachment.owner_user_id)
        assert result["path"] == "/local/path"

    async def test_get_download_response_not_found(self, service, mock_repo):
        mock_repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(AttachmentNotFoundException):
            await service.get_download_response(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.uuid4())

    async def test_get_download_response_access_denied(self, service, mock_repo):
        attachment = _make_attachment(owner_user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"))
        mock_repo.get_by_id = AsyncMock(return_value=attachment)
        with pytest.raises(AttachmentAccessDeniedException):
            await service.get_download_response(attachment.id, uuid.UUID("87654321-4321-8765-4321-876543218765"))

    async def test_get_download_response_missing_storage_file(self, service, mock_repo, mock_storage):
        attachment = _make_attachment(storage_path="/missing/path")
        mock_repo.get_by_id = AsyncMock(return_value=attachment)
        mock_storage.exists = MagicMock(return_value=False)
        with pytest.raises(AttachmentNotFoundException):
            await service.get_download_response(attachment.id, attachment.owner_user_id)


class TestAttachmentServiceMetadata:
    async def test_get_metadata_success(self, service, mock_repo):
        attachment = _make_attachment()
        mock_repo.get_by_id = AsyncMock(return_value=attachment)
        result = await service.get_metadata(attachment.id, attachment.owner_user_id)
        assert result == attachment

    async def test_get_metadata_not_found(self, service, mock_repo):
        mock_repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(AttachmentNotFoundException):
            await service.get_metadata(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.uuid4())

    async def test_get_metadata_access_denied(self, service, mock_repo):
        attachment = _make_attachment(owner_user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"))
        mock_repo.get_by_id = AsyncMock(return_value=attachment)
        with pytest.raises(AttachmentAccessDeniedException):
            await service.get_metadata(attachment.id, uuid.UUID("87654321-4321-8765-4321-876543218765"))


class TestAttachmentServiceList:
    async def test_list_for_entity_filters_by_owner(self, service, mock_repo):
        owner = uuid.UUID("87654321-4321-8765-4321-876543218765")
        other = uuid.UUID("00000000-0000-0000-0000-000000000000")
        a1 = _make_attachment(entity_type=AttachmentEntityType.TASK, entity_id=uuid.UUID("11111111-1111-1111-1111-111111111111"), owner_user_id=owner)
        a2 = _make_attachment(entity_type=AttachmentEntityType.TASK, entity_id=uuid.UUID("11111111-1111-1111-1111-111111111111"), owner_user_id=other)
        mock_repo.list_for_entity = AsyncMock(return_value=[a1, a2])
        result = await service.list_for_entity(AttachmentEntityType.TASK, uuid.UUID("11111111-1111-1111-1111-111111111111"), owner)
        assert len(result) == 1
        assert result[0].owner_user_id == owner

    async def test_list_all_for_entity_no_filter(self, service, mock_repo, sample_attachment):
        mock_repo.list_for_entity = AsyncMock(return_value=[sample_attachment])
        result = await service.list_all_for_entity(AttachmentEntityType.TASK, sample_attachment.entity_id)
        assert result == [sample_attachment]

    async def test_list_recent_for_user(self, service, mock_repo, sample_attachment):
        mock_repo.list_recent_for_user = AsyncMock(return_value=[sample_attachment])
        result = await service.list_recent_for_user(sample_attachment.owner_user_id, limit=5)
        assert len(result) == 1


class TestAttachmentServiceDelete:
    async def test_delete_success(self, service, mock_repo, mock_storage):
        attachment = _make_attachment(storage_path="/attachments/tasks/123/report.pdf")
        mock_repo.get_by_id = AsyncMock(return_value=attachment)
        mock_storage.delete_file = AsyncMock(return_value=True)
        mock_repo.delete = AsyncMock()
        await service.delete(attachment.id, attachment.owner_user_id)
        mock_storage.delete_file.assert_called_once_with(attachment.storage_path)
        mock_repo.delete.assert_called_once_with(attachment)

    async def test_delete_not_found(self, service, mock_repo):
        mock_repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(AttachmentNotFoundException):
            await service.delete(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.uuid4())

    async def test_delete_access_denied(self, service, mock_repo):
        attachment = _make_attachment(owner_user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"))
        mock_repo.get_by_id = AsyncMock(return_value=attachment)
        with pytest.raises(AttachmentAccessDeniedException):
            await service.delete(attachment.id, uuid.UUID("87654321-4321-8765-4321-876543218765"))

    async def test_delete_swallows_storage_error(self, service, mock_repo, mock_storage):
        attachment = _make_attachment(storage_path="/missing")
        mock_repo.get_by_id = AsyncMock(return_value=attachment)
        mock_storage.delete_file = AsyncMock(side_effect=Exception("file not found"))
        mock_repo.delete = AsyncMock()
        await service.delete(attachment.id, attachment.owner_user_id)
        mock_repo.delete.assert_called_once()


class TestAttachmentServiceVerifiedMethods:
    async def test_get_for_download_verified_success(self, service, mock_repo, mock_storage):
        attachment = _make_attachment(storage_path="/attachments/tasks/123/report.pdf")
        mock_repo.get_by_id = AsyncMock(return_value=attachment)
        mock_storage.exists = MagicMock(return_value=True)
        result = await service.get_for_download_verified(
            attachment.id, AttachmentEntityType.TASK, attachment.entity_id
        )
        assert result == attachment

    async def test_get_for_download_verified_wrong_entity_raises(self, service, mock_repo):
        attachment = _make_attachment(entity_type=AttachmentEntityType.TASK)
        mock_repo.get_by_id = AsyncMock(return_value=attachment)
        mock_storage.provider_name = "local"
        service._storage = mock_storage
        with pytest.raises(AttachmentNotFoundException):
            await service.get_for_download_verified(
                attachment.id, AttachmentEntityType.CALENDAR_EVENT, uuid.UUID("99999999-9999-9999-9999-999999999999")
            )

    async def test_delete_verified_success(self, service, mock_repo, mock_storage):
        attachment = _make_attachment(storage_path="/attachments/tasks/123/report.pdf")
        mock_repo.get_by_id = AsyncMock(return_value=attachment)
        mock_storage.delete_file = AsyncMock(return_value=True)
        mock_repo.delete = AsyncMock()
        await service.delete_verified(attachment.id, AttachmentEntityType.TASK, attachment.entity_id)
        mock_repo.delete.assert_called_once_with(attachment)

    async def test_delete_verified_swallows_storage_error(self, service, mock_repo, mock_storage):
        attachment = _make_attachment(storage_path="/missing")
        mock_repo.get_by_id = AsyncMock(return_value=attachment)
        mock_storage.delete_file = AsyncMock(side_effect=Exception("missing"))
        mock_repo.delete = AsyncMock()
        await service.delete_verified(attachment.id, AttachmentEntityType.TASK, attachment.entity_id)
        mock_repo.delete.assert_called_once_with(attachment)


class TestAttachmentServiceBulkDelete:
    async def test_delete_all_for_entity_success(self, service, mock_repo, mock_storage):
        attachment = _make_attachment(storage_path="/attachments/tasks/123/report.pdf")
        mock_repo.delete_all_for_entity = AsyncMock(return_value=[attachment])
        mock_storage.delete_file = AsyncMock(return_value=True)
        await service.delete_all_for_entity(AttachmentEntityType.TASK, attachment.entity_id)
        mock_storage.delete_file.assert_called_once_with(attachment.storage_path)

    async def test_delete_all_for_entity_swallows_storage_error(self, service, mock_repo, mock_storage):
        attachment = _make_attachment(storage_path="/missing")
        mock_repo.delete_all_for_entity = AsyncMock(return_value=[attachment])
        mock_storage.delete_file = AsyncMock(side_effect=Exception("missing"))
        await service.delete_all_for_entity(AttachmentEntityType.TASK, attachment.entity_id)
        mock_storage.delete_file.assert_called_once()

    async def test_delete_all_for_entity_empty(self, service, mock_repo):
        mock_repo.delete_all_for_entity = AsyncMock(return_value=[])
        await service.delete_all_for_entity(AttachmentEntityType.TASK, uuid.UUID("99999999-9999-9999-9999-999999999999"))
        mock_repo.delete_all_for_entity.assert_called_once()


class TestAttachmentServiceFetchAndAuthorise:
    async def test_fetch_and_authorise_success(self, service, mock_repo):
        attachment = _make_attachment()
        mock_repo.get_by_id = AsyncMock(return_value=attachment)
        result = await service._fetch_and_authorise(attachment.id, attachment.owner_user_id)
        assert result == attachment

    async def test_fetch_and_authorise_not_found_raises(self, service, mock_repo):
        mock_repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(AttachmentNotFoundException):
            await service._fetch_and_authorise(uuid.UUID("12345678-1234-5678-1234-567812345678"), uuid.uuid4())

    async def test_fetch_and_authorise_access_denied_raises(self, service, mock_repo):
        attachment = _make_attachment(owner_user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"))
        mock_repo.get_by_id = AsyncMock(return_value=attachment)
        with pytest.raises(AttachmentAccessDeniedException):
            await service._fetch_and_authorise(attachment.id, uuid.UUID("87654321-4321-8765-4321-876543218765"))
