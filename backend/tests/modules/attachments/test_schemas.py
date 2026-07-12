import uuid
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.modules.attachments.enums import AttachmentEntityType
from app.modules.attachments.schemas import (
    AttachmentUploadContext,
    PresignedUploadRequest,
    ConfirmUploadRequest,
    PresignedUploadResponse,
    AttachmentResponse,
    AttachmentListResponse,
)


class TestAttachmentUploadContext:
    def test_minimal_valid(self):
        ctx = AttachmentUploadContext(
            entity_type=AttachmentEntityType.TASK,
            entity_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        )
        assert ctx.entity_type == AttachmentEntityType.TASK
        assert ctx.entity_id == uuid.UUID("12345678-1234-5678-1234-567812345678")

    def test_requires_entity_type(self):
        with pytest.raises(ValidationError):
            AttachmentUploadContext(entity_id=uuid.uuid4())

    def test_requires_entity_id(self):
        with pytest.raises(ValidationError):
            AttachmentUploadContext(entity_type=AttachmentEntityType.TASK)


class TestPresignedUploadRequest:
    def test_minimal_valid(self):
        payload = PresignedUploadRequest(
            entity_type=AttachmentEntityType.TASK,
            entity_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            filename="report.pdf",
            content_type="application/pdf",
        )
        assert payload.filename == "report.pdf"
        assert payload.content_type == "application/pdf"

    def test_filename_max_length(self):
        long_name = "a" * 255
        payload = PresignedUploadRequest(
            entity_type=AttachmentEntityType.TASK,
            entity_id=uuid.uuid4(),
            filename=long_name,
            content_type="application/pdf",
        )
        assert len(payload.filename) == 255

    def test_filename_too_long_raises(self):
        with pytest.raises(ValidationError):
            PresignedUploadRequest(
                entity_type=AttachmentEntityType.TASK,
                entity_id=uuid.uuid4(),
                filename="a" * 256,
                content_type="application/pdf",
            )

    def test_empty_filename_raises(self):
        with pytest.raises(ValidationError):
            PresignedUploadRequest(
                entity_type=AttachmentEntityType.TASK,
                entity_id=uuid.uuid4(),
                filename="",
                content_type="application/pdf",
            )

    def test_empty_content_type_raises(self):
        with pytest.raises(ValidationError):
            PresignedUploadRequest(
                entity_type=AttachmentEntityType.TASK,
                entity_id=uuid.uuid4(),
                filename="file.pdf",
                content_type="",
            )


class TestConfirmUploadRequest:
    def test_minimal_valid(self):
        payload = ConfirmUploadRequest(
            entity_type=AttachmentEntityType.CALENDAR_EVENT,
            entity_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            key="calendar_events/abc/file.pdf",
            original_filename="file.pdf",
            content_type="application/pdf",
            size=1024,
        )
        assert payload.size == 1024
        assert payload.key == "calendar_events/abc/file.pdf"

    def test_size_must_be_positive(self):
        with pytest.raises(ValidationError):
            ConfirmUploadRequest(
                entity_type=AttachmentEntityType.TASK,
                entity_id=uuid.uuid4(),
                key="tasks/abc/file.pdf",
                original_filename="file.pdf",
                content_type="application/pdf",
                size=0,
            )

    def test_size_negative_raises(self):
        with pytest.raises(ValidationError):
            ConfirmUploadRequest(
                entity_type=AttachmentEntityType.TASK,
                entity_id=uuid.uuid4(),
                key="tasks/abc/file.pdf",
                original_filename="file.pdf",
                content_type="application/pdf",
                size=-1,
            )

    def test_empty_key_raises(self):
        with pytest.raises(ValidationError):
            ConfirmUploadRequest(
                entity_type=AttachmentEntityType.TASK,
                entity_id=uuid.uuid4(),
                key="",
                original_filename="file.pdf",
                content_type="application/pdf",
                size=1024,
            )


class TestPresignedUploadResponse:
    def test_minimal_valid(self):
        resp = PresignedUploadResponse(
            upload_url="https://s3.amazonaws.com/bucket/key",
            key="tasks/abc/file.pdf",
            expires_in=3600,
        )
        assert resp.expires_in == 3600
        assert resp.upload_url.startswith("https://")


class TestAttachmentResponse:
    def _make_attachment(self, **kwargs):
        now = datetime.now(timezone.utc)
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
            created_at=now,
            updated_at=now,
        )

    def test_minimal_fields(self):
        attachment = self._make_attachment()
        assert attachment.extension == "pdf"
        assert attachment.size == 1024
        assert attachment.storage_provider == "local"

    def test_all_entity_types(self):
        for entity_type in AttachmentEntityType:
            attachment = self._make_attachment(entity_type=entity_type)
            assert attachment.entity_type == entity_type

    def test_model_validate_from_orm_like_dict(self):
        data = {
            "id": uuid.UUID("12345678-1234-5678-1234-567812345678"),
            "owner_user_id": uuid.UUID("87654321-4321-8765-4321-876543218765"),
            "entity_type": AttachmentEntityType.TASK,
            "entity_id": uuid.UUID("12345678-1234-5678-1234-567812345678"),
            "original_filename": "doc.pdf",
            "stored_filename": "a1b2_doc.pdf",
            "content_type": "application/pdf",
            "extension": "pdf",
            "size": 2048,
            "storage_provider": "s3",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        attachment = AttachmentResponse(**data)
        assert attachment.stored_filename == "a1b2_doc.pdf"
        assert attachment.storage_provider == "s3"


class TestAttachmentListResponse:
    def test_empty_list(self):
        resp = AttachmentListResponse(attachments=[], total_count=0)
        assert resp.total_count == 0
        assert len(resp.attachments) == 0

    def test_with_attachments(self):
        attachment = AttachmentResponse(
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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        resp = AttachmentListResponse(attachments=[attachment], total_count=1)
        assert resp.total_count == 1
        assert len(resp.attachments) == 1
        assert resp.attachments[0].extension == "pdf"

    def test_total_count_mismatch_allowed(self):
        attachment = AttachmentResponse(
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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        resp = AttachmentListResponse(attachments=[attachment], total_count=5)
        assert resp.total_count == 5
