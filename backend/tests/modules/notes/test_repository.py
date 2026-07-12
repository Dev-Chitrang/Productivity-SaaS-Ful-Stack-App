import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, and_, or_, asc, desc, func
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.notes.repository import NoteRepository
from app.models.notes import Note
from app.modules.notes.constants import MAX_NOTE_CONTENT_LENGTH


@pytest.fixture
def repo():
    db = AsyncMock(spec=AsyncSession)
    return NoteRepository(db)


def _make_note(**kwargs):
    now = datetime.now(timezone.utc)
    return Note(
        id=kwargs.get("id", uuid.UUID("12345678-1234-5678-1234-567812345678")),
        user_id=kwargs.get("user_id", uuid.UUID("87654321-4321-8765-4321-876543218765")),
        title=kwargs.get("title", "Test Note"),
        content=kwargs.get("content", "Content here"),
        category=kwargs.get("category", "personal"),
        tags=kwargs.get("tags", []),
        is_pinned=kwargs.get("is_pinned", False),
        is_favorite=kwargs.get("is_favorite", False),
        is_archived=kwargs.get("is_archived", False),
        deleted_at=kwargs.get("deleted_at", None),
        created_at=kwargs.get("created_at", now),
        updated_at=kwargs.get("updated_at", now),
    )


class TestNoteRepositoryCreate:
    async def test_create_success(self, repo):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_data = {"title": "New Note", "content": "Content", "tags": ["work"]}
        result = await repo.create(user_id, note_data)
        assert result.user_id == user_id
        assert result.title == "New Note"
        repo.db.add.assert_called_once()
        repo.db.flush.assert_called_once()

    async def test_create_rollback_on_exception(self, repo):
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.create(uuid.UUID("87654321-4321-8765-4321-876543218765"), {"content": "x"})
        repo.db.rollback.assert_called_once()


class TestNoteRepositoryGetById:
    async def test_get_by_id_found(self, repo):
        note = _make_note()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = note
        repo.db.execute.return_value = result_mock

        found = await repo.get_by_id(note.id)
        assert found == note

    async def test_get_by_id_not_found(self, repo):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        repo.db.execute.return_value = result_mock

        found = await repo.get_by_id(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert found is None

    async def test_get_by_id_excludes_soft_deleted_by_default(self, repo):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        repo.db.execute.return_value = result_mock

        await repo.get_by_id(uuid.UUID("12345678-1234-5678-1234-567812345678"), include_deleted=False)
        stmt = repo.db.execute.call_args[0][0]
        assert "deleted_at" in str(stmt)

    async def test_get_by_id_includes_deleted_when_requested(self, repo):
        note = _make_note(deleted_at=datetime.now(timezone.utc))
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = note
        repo.db.execute.return_value = result_mock

        found = await repo.get_by_id(note.id, include_deleted=True)
        assert found == note


class TestNoteRepositoryUpdate:
    async def test_update_success(self, repo):
        note = _make_note()
        update_data = {"title": "Updated", "category": "work"}
        result = await repo.update(note, update_data)
        assert result.title == "Updated"
        assert result.category == "work"
        repo.db.add.assert_called_once_with(note)
        repo.db.flush.assert_called_once()

    async def test_update_partial_fields(self, repo):
        note = _make_note()
        update_data = {"title": "Updated"}
        result = await repo.update(note, update_data)
        assert result.title == "Updated"
        assert result.category == "personal"

    async def test_update_rollback_on_exception(self, repo):
        note = _make_note()
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.update(note, {"title": "Updated"})
        repo.db.rollback.assert_called_once()


class TestNoteRepositorySoftDelete:
    async def test_soft_delete_success(self, repo):
        note = _make_note(deleted_at=None)
        now = datetime.now(timezone.utc)
        result = await repo.soft_delete(note)
        assert result is None
        assert note.deleted_at is not None
        assert note.deleted_at >= now - timedelta(seconds=2)
        repo.db.add.assert_called_once_with(note)
        repo.db.flush.assert_called_once()

    async def test_soft_delete_rollback_on_exception(self, repo):
        note = _make_note()
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.soft_delete(note)
        repo.db.rollback.assert_called_once()


class TestNoteRepositoryRestore:
    async def test_restore_success(self, repo):
        note = _make_note(deleted_at=datetime.now(timezone.utc))
        result = await repo.restore(note)
        assert result.deleted_at is None
        repo.db.add.assert_called_once_with(note)
        repo.db.flush.assert_called_once()

    async def test_restore_rollback_on_exception(self, repo):
        note = _make_note(deleted_at=datetime.now(timezone.utc))
        repo.db.add.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await repo.restore(note)
        repo.db.rollback.assert_called_once()


class TestNoteRepositoryGetAnalytics:
    async def test_get_analytics_returns_dict(self, repo):
        repo.db.scalar.return_value = 5
        repo.db.execute.return_value = MagicMock()

        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        result = await repo.get_analytics(user_id)

        assert "total" in result
        assert "favorite" in result
        assert "archived" in result
        assert "recent_notes" in result
        assert "monthly_created" in result

    async def test_get_analytics_counts(self, repo):
        repo.db.scalar.side_effect = [10, 2, 3]
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        result = await repo.get_analytics(user_id)

        assert result["total"] == 10
        assert result["favorite"] == 2
        assert result["archived"] == 3

    async def test_get_analytics_recent_notes_structure(self, repo):
        repo.db.scalar.return_value = 0
        mock_row = MagicMock()
        mock_row.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_row.title = "Recent Note"
        mock_row.updated_at = datetime.now(timezone.utc)
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = [mock_row]

        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        result = await repo.get_analytics(user_id)

        assert len(result["recent_notes"]) == 1
        assert result["recent_notes"][0]["title"] == "Recent Note"


class TestNoteRepositoryListAndFilter:
    async def test_list_returns_sequence(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        result = await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"))
        assert isinstance(result, list)

    async def test_list_filters_by_user(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"))
        stmt = repo.db.execute.call_args[0][0]
        assert "user_id" in str(stmt)

    async def test_list_excludes_deleted_by_default(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"))
        stmt = repo.db.execute.call_args[0][0]
        assert "deleted_at" in str(stmt)

    async def test_list_includes_deleted_when_true(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), deleted=True)
        stmt = repo.db.execute.call_args[0][0]
        assert "deleted_at" in str(stmt)

    async def test_list_search_query(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), search="meeting")
        stmt = repo.db.execute.call_args[0][0]
        compiled = stmt.compile(compile_kwargs={"literal_binds": True})
        assert "%meeting%" in str(compiled)

    async def test_list_category_exact_match(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), category="personal")
        stmt = repo.db.execute.call_args[0][0]
        compiled = stmt.compile(compile_kwargs={"literal_binds": True})
        assert "'personal'" in str(compiled).lower()

    async def test_list_tag_contains(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), tag="work")
        stmt = repo.db.execute.call_args[0][0]
        assert "tags" in str(stmt).lower()
        assert "@>" in str(stmt)

    async def test_list_favorite_filter(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), favorite=True)
        stmt = repo.db.execute.call_args[0][0]
        assert "is_favorite" in str(stmt)

    async def test_list_pinned_filter(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), pinned=True)
        stmt = repo.db.execute.call_args[0][0]
        assert "is_pinned" in str(stmt)

    async def test_list_archived_filter(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), archived=True)
        stmt = repo.db.execute.call_args[0][0]
        assert "is_archived" in str(stmt)

    async def test_list_sort_by_updated_at_desc(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), sort_by="updated_at", sort_order="desc")
        stmt = repo.db.execute.call_args[0][0]
        assert "updated_at" in str(stmt)

    async def test_list_sort_by_title_asc(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), sort_by="title", sort_order="asc")
        stmt = repo.db.execute.call_args[0][0]
        assert "title" in str(stmt)

    async def test_list_invalid_sort_falls_back_to_updated_at(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.list_and_filter(uuid.UUID("87654321-4321-8765-4321-876543218765"), sort_by="invalid_column")
        stmt = repo.db.execute.call_args[0][0]
        assert "updated_at" in str(stmt)
