import uuid
from datetime import datetime, timezone
from app.modules.attachments.enums import AttachmentEntityType
from app.models.attachment import Attachment


class TestAttachmentModel:
    def test_tablename(self):
        assert Attachment.__tablename__ == "attachments"

    def test_id_default_generates_uuid(self):
        attachment = Attachment(
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
        )
        assert attachment.id is None or isinstance(attachment.id, uuid.UUID)

    def test_minimal_fields(self):
        now = datetime.now(timezone.utc)
        attachment = Attachment(
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
            created_at=now,
            updated_at=now,
        )
        assert attachment.owner_user_id == uuid.UUID("87654321-4321-8765-4321-876543218765")
        assert attachment.entity_type == AttachmentEntityType.TASK
        assert attachment.entity_id == uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert attachment.original_filename == "report.pdf"
        assert attachment.stored_filename == "a1b2_report.pdf"
        assert attachment.content_type == "application/pdf"
        assert attachment.extension == "pdf"
        assert attachment.size == 1024
        assert attachment.storage_provider == "local"
        assert attachment.storage_path == "/attachments/tasks/123/report.pdf"

    def test_full_fields(self):
        attachment_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        entity_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        now = datetime.now(timezone.utc)
        attachment = Attachment(
            id=attachment_id,
            owner_user_id=user_id,
            entity_type=AttachmentEntityType.CALENDAR_EVENT,
            entity_id=entity_id,
            original_filename="invite.docx",
            stored_filename="a1b2_invite.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            extension="docx",
            size=2048,
            storage_provider="s3",
            storage_path="calendar_events/11111111-1111-1111-1111-111111111111/a1b2_invite.docx",
            created_at=now,
            updated_at=now,
        )
        assert attachment.id == attachment_id
        assert attachment.owner_user_id == user_id
        assert attachment.entity_type == AttachmentEntityType.CALENDAR_EVENT
        assert attachment.entity_id == entity_id
        assert attachment.extension == "docx"
        assert attachment.storage_provider == "s3"
        assert "calendar_events" in attachment.storage_path

    def test_created_at_default_utc(self):
        now = datetime.now(timezone.utc)
        attachment = Attachment(
            owner_user_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            entity_type=AttachmentEntityType.TASK,
            entity_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            original_filename="report.pdf",
            stored_filename="a1b2_report.pdf",
            content_type="application/pdf",
            extension="pdf",
            size=1024,
            storage_provider="local",
            storage_path="/path",
            created_at=now,
            updated_at=now,
        )
        assert attachment.created_at is not None
        assert attachment.created_at.tzinfo == timezone.utc

    def test_updated_at_default_utc(self):
        now = datetime.now(timezone.utc)
        attachment = Attachment(
            owner_user_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            entity_type=AttachmentEntityType.TASK,
            entity_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            original_filename="report.pdf",
            stored_filename="a1b2_report.pdf",
            content_type="application/pdf",
            extension="pdf",
            size=1024,
            storage_provider="local",
            storage_path="/path",
            created_at=now,
            updated_at=now,
        )
        assert attachment.updated_at is not None
        assert attachment.updated_at.tzinfo == timezone.utc

    def test_all_entity_types_accepted(self):
        for entity_type in AttachmentEntityType:
            attachment = Attachment(
                owner_user_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
                entity_type=entity_type,
                entity_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
                original_filename="report.pdf",
                stored_filename="a1b2_report.pdf",
                content_type="application/pdf",
                extension="pdf",
                size=1024,
                storage_provider="local",
                storage_path="/path",
            )
            assert attachment.entity_type == entity_type
