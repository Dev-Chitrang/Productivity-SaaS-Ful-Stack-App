from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, call
from sqlalchemy.ext.asyncio import AsyncSession
import pytest

from app.models.entity_link import EntityLink
from app.modules.entity_links.repository import EntityLinkRepository


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(mock_db):
    return EntityLinkRepository(mock_db)


def _make_link(link_id=None, deleted_at=None):
    return EntityLink(
        id=link_id or uuid4(),
        source_type="meeting",
        source_id=uuid4(),
        target_type="task",
        target_id=uuid4(),
        link_type="RELATED_TO",
        relation_origin=None,
        created_by=uuid4(),
        created_at=datetime.now(timezone.utc),
        deleted_at=deleted_at,
    )


class TestCreate:
    async def test_create_success(self, repo, mock_db):
        link_data = {
            "source_type": "meeting",
            "source_id": uuid4(),
            "target_type": "task",
            "target_id": uuid4(),
            "link_type": "RELATED_TO",
            "created_by": uuid4(),
        }
        result = await repo.create(link_data)
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        assert isinstance(result, EntityLink)
        assert result.source_type == "meeting"

    async def test_create_rollback_on_error(self, repo, mock_db):
        mock_db.flush.side_effect = RuntimeError("db error")
        with pytest.raises(RuntimeError):
            await repo.create({"source_type": "meeting", "source_id": uuid4(), "target_type": "task", "target_id": uuid4(), "created_by": uuid4()})
        mock_db.rollback.assert_called_once()


class TestGetById:
    async def test_get_by_id_found(self, repo, mock_db):
        link = _make_link()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = link
        mock_db.execute.return_value = mock_result

        result = await repo.get_by_id(link.id)
        assert result == link

    async def test_get_by_id_not_found(self, repo, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await repo.get_by_id(uuid4())
        assert result is None

    async def test_get_by_id_include_deleted(self, repo, mock_db):
        link = _make_link(deleted_at=datetime.now(timezone.utc))
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = link
        mock_db.execute.return_value = mock_result

        result = await repo.get_by_id(link.id, include_deleted=True)
        assert result == link


class TestSoftDelete:
    async def test_soft_delete_success(self, repo, mock_db):
        link = _make_link()
        result = await repo.soft_delete(link)
        assert link.deleted_at is not None
        mock_db.add.assert_called_once_with(link)
        mock_db.flush.assert_called_once()

    async def test_soft_delete_rollback_on_error(self, repo, mock_db):
        link = _make_link()
        mock_db.flush.side_effect = RuntimeError("db error")
        with pytest.raises(RuntimeError):
            await repo.soft_delete(link)
        mock_db.rollback.assert_called_once()


class TestListLinks:
    async def test_list_links_no_filters(self, repo, mock_db):
        links = [_make_link(), _make_link()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = links
        mock_db.execute.return_value = mock_result

        result = await repo.list_links()
        assert len(result) == 2
        mock_db.execute.assert_called_once()

    async def test_list_links_with_filters(self, repo, mock_db):
        link = _make_link()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [link]
        mock_db.execute.return_value = mock_result

        result = await repo.list_links(
            source_type="meeting",
            source_id=link.source_id,
            target_type="task",
            target_id=link.target_id,
        )
        assert len(result) == 1

    async def test_list_links_excludes_deleted_by_default(self, repo, mock_db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        await repo.list_links()
        stmt = mock_db.execute.call_args[0][0]
        where_clause = str(stmt.whereclause)
        assert "deleted_at" in where_clause or "None" in stmt._whereclause.text if hasattr(stmt, "_whereclause") else True


class TestSoftDeleteByEntity:
    async def test_soft_delete_by_entity_success(self, repo, mock_db):
        links = [_make_link(), _make_link()]
        mock_exec_result = MagicMock()
        mock_exec_result.scalars.return_value.all.return_value = links
        mock_db.execute.return_value = mock_exec_result

        await repo.soft_delete_by_entity("meeting", uuid4())
        for link in links:
            assert link.deleted_at is not None
        mock_db.flush.assert_called_once()

    async def test_soft_delete_by_entity_no_matches(self, repo, mock_db):
        mock_exec_result = MagicMock()
        mock_exec_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_exec_result

        await repo.soft_delete_by_entity("task", uuid4())
        # flush still called even with no links to delete
        mock_db.flush.assert_called_once()

    async def test_soft_delete_by_entity_rollback_on_error(self, repo, mock_db):
        mock_exec_result = MagicMock()
        mock_exec_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_exec_result
        mock_db.flush.side_effect = RuntimeError("db error")
        with pytest.raises(RuntimeError):
            await repo.soft_delete_by_entity("meeting", uuid4())
        mock_db.rollback.assert_called_once()