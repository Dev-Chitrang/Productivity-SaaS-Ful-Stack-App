import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.attachment import Attachment
from app.modules.attachments.enums import AttachmentEntityType
from app.modules.attachments.repository import AttachmentRepository


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(mock_db):
    return AttachmentRepository(mock_db)


@pytest.fixture
def sample_attachment():
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
        storage_path="/attachments/tasks/12345678/report.pdf",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestAttachmentRepositoryCreate:
    async def test_create_success(self, repo, mock_db, sample_attachment):
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        result = await repo.create({
            "owner_user_id": sample_attachment.owner_user_id,
            "entity_type": sample_attachment.entity_type,
            "entity_id": sample_attachment.entity_id,
            "original_filename": "report.pdf",
            "stored_filename": "a1b2_report.pdf",
            "content_type": "application/pdf",
            "extension": "pdf",
            "size": 1024,
            "storage_provider": "local",
            "storage_path": "/path",
        })
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    async def test_create_rollback_on_exception(self, repo, mock_db):
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock(side_effect=Exception("DB error"))
        mock_db.rollback = AsyncMock()
        with pytest.raises(Exception, match="DB error"):
            await repo.create({})
        mock_db.rollback.assert_called_once()


class TestAttachmentRepositoryDelete:
    async def test_delete_success(self, repo, mock_db, sample_attachment):
        mock_db.delete = AsyncMock()
        mock_db.flush = AsyncMock()
        await repo.delete(sample_attachment)
        mock_db.delete.assert_called_once_with(sample_attachment)
        mock_db.flush.assert_called_once()

    async def test_delete_rollback_on_exception(self, repo, mock_db, sample_attachment):
        mock_db.delete = AsyncMock()
        mock_db.flush = AsyncMock(side_effect=Exception("DB error"))
        mock_db.rollback = AsyncMock()
        with pytest.raises(Exception, match="DB error"):
            await repo.delete(sample_attachment)
        mock_db.rollback.assert_called_once()


class TestAttachmentRepositoryGetById:
    async def test_get_by_id_found(self, repo, mock_db, sample_attachment):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_attachment
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await repo.get_by_id(sample_attachment.id)
        assert result == sample_attachment

    async def test_get_by_id_not_found(self, repo, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await repo.get_by_id(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert result is None


class TestAttachmentRepositoryListForEntity:
    async def test_list_for_entity_success(self, repo, mock_db, sample_attachment):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_attachment]
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await repo.list_for_entity(AttachmentEntityType.TASK, sample_attachment.entity_id)
        assert result == [sample_attachment]
        assert len(result) == 1

    async def test_list_for_entity_empty(self, repo, mock_db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await repo.list_for_entity(AttachmentEntityType.TASK, uuid.uuid4())
        assert result == []


class TestAttachmentRepositoryListForUser:
    async def test_list_for_user_all(self, repo, mock_db, sample_attachment):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_attachment]
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await repo.list_for_user(sample_attachment.owner_user_id)
        assert result == [sample_attachment]

    async def test_list_for_user_filtered_by_entity_type(self, repo, mock_db, sample_attachment):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_attachment]
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await repo.list_for_user(sample_attachment.owner_user_id, AttachmentEntityType.TASK)
        assert result == [sample_attachment]

    async def test_list_for_user_no_results(self, repo, mock_db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await repo.list_for_user(uuid.UUID("87654321-4321-8765-4321-876543218765"))
        assert result == []


class TestAttachmentRepositoryListRecentForUser:
    async def test_list_recent_default_limit(self, repo, mock_db, sample_attachment):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_attachment]
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await repo.list_recent_for_user(sample_attachment.owner_user_id)
        assert result == [sample_attachment]

    async def test_list_recent_custom_limit(self, repo, mock_db, sample_attachment):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_attachment]
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await repo.list_recent_for_user(sample_attachment.owner_user_id, limit=5)
        assert result == [sample_attachment]

    async def test_list_recent_empty(self, repo, mock_db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await repo.list_recent_for_user(uuid.UUID("87654321-4321-8765-4321-876543218765"))
        assert result == []


class TestAttachmentRepositoryStoredFilenameExists:
    async def test_duplicate_exists(self, repo, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_db.execute = AsyncMock(return_value=mock_result)
        assert await repo.stored_filename_exists(
            AttachmentEntityType.TASK,
            uuid.UUID("12345678-1234-5678-1234-567812345678"),
            "a1b2_file.pdf",
        ) is True

    async def test_no_duplicate(self, repo, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        assert await repo.stored_filename_exists(
            AttachmentEntityType.TASK,
            uuid.UUID("12345678-1234-5678-1234-567812345678"),
            "unique_file.pdf",
        ) is False


class TestAttachmentRepositoryDeleteAllForEntity:
    async def test_delete_all_success(self, repo, mock_db, sample_attachment):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_attachment]
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.delete = AsyncMock()
        mock_db.flush = AsyncMock()
        deleted = await repo.delete_all_for_entity(AttachmentEntityType.TASK, sample_attachment.entity_id)
        assert len(deleted) == 1
        mock_db.delete.assert_called_once_with(sample_attachment)
        mock_db.flush.assert_called_once()

    async def test_delete_all_empty(self, repo, mock_db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()
        deleted = await repo.delete_all_for_entity(AttachmentEntityType.TASK, uuid.uuid4())
        assert deleted == []
        mock_db.flush.assert_not_called()

    async def test_delete_all_rollback_on_exception(self, repo, mock_db, sample_attachment):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_attachment]
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.delete = AsyncMock(side_effect=Exception("DB error"))
        mock_db.rollback = AsyncMock()
        with pytest.raises(Exception, match="DB error"):
            await repo.delete_all_for_entity(AttachmentEntityType.TASK, sample_attachment.entity_id)
        mock_db.rollback.assert_called_once()
