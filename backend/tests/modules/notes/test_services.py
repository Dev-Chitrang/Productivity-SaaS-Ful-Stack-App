import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.modules.notes.exceptions import (
    NoteNotFoundException,
    NoteAccessDeniedException,
    NoteValidationError,
)
from app.modules.notes.repository import NoteRepository
from app.modules.notes.services import NoteService
from app.modules.notes.schemas import NoteCreate, NoteUpdate
from app.models.notes import Note


@pytest.fixture
def repo():
    return MagicMock(spec=NoteRepository)


@pytest.fixture
def service(repo):
    return NoteService(repo)


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


class TestGetNote:
    async def test_get_note_success(self, service, repo):
        note = _make_note()
        repo.get_by_id.return_value = note

        result = await service.get_note(note.user_id, note.id)
        assert result == note
        repo.get_by_id.assert_called_once_with(note.id, include_deleted=False)

    async def test_get_note_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(NoteNotFoundException):
            await service.get_note(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"))

    async def test_get_note_access_denied(self, service, repo):
        note = _make_note(user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"))
        repo.get_by_id.return_value = note
        with pytest.raises(NoteAccessDeniedException):
            await service.get_note(uuid.UUID("87654321-4321-8765-4321-876543218765"), note.id)

    async def test_get_note_includes_deleted_when_flag_true(self, service, repo):
        note = _make_note(deleted_at=datetime.now(timezone.utc))
        repo.get_by_id.return_value = note

        result = await service.get_note(note.user_id, note.id, include_deleted=True)
        assert result == note
        repo.get_by_id.assert_called_once_with(note.id, include_deleted=True)


class TestCreateNote:
    async def test_create_note_success(self, service, repo):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        payload = NoteCreate(title="New Note", content="Content", tags=["work"])
        repo.create.return_value = _make_note()

        result = await service.create_note(user_id, payload)
        repo.create.assert_called_once_with(user_id, payload.model_dump())


class TestUpdateNote:
    async def test_update_note_success(self, service, repo):
        note = _make_note()
        repo.get_by_id.return_value = note
        repo.update.return_value = note

        payload = NoteUpdate(title="Updated Title", category="work")
        result = await service.update_note(note.user_id, note.id, payload)
        repo.update.assert_called_once()
        assert result == note

    async def test_update_note_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        payload = NoteUpdate(title="Updated")
        with pytest.raises(NoteNotFoundException):
            await service.update_note(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"), payload)

    async def test_update_note_access_denied(self, service, repo):
        note = _make_note(user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"))
        repo.get_by_id.return_value = note
        payload = NoteUpdate(title="Updated")
        with pytest.raises(NoteAccessDeniedException):
            await service.update_note(uuid.UUID("87654321-4321-8765-4321-876543218765"), note.id, payload)

    async def test_update_note_excludes_unset_fields(self, service, repo):
        note = _make_note()
        repo.get_by_id.return_value = note
        repo.update.return_value = note

        payload = NoteUpdate(title="Updated Title")
        await service.update_note(note.user_id, note.id, payload)
        repo.update.assert_called_once_with(note, {"title": "Updated Title"})


class TestDeleteNote:
    async def test_delete_note_success(self, service, repo):
        note = _make_note()
        repo.get_by_id.return_value = note

        await service.delete_note(note.user_id, note.id)
        repo.soft_delete.assert_called_once_with(note)

    async def test_delete_note_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(NoteNotFoundException):
            await service.delete_note(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"))

    async def test_delete_note_access_denied(self, service, repo):
        note = _make_note(user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"))
        repo.get_by_id.return_value = note
        with pytest.raises(NoteAccessDeniedException):
            await service.delete_note(uuid.UUID("87654321-4321-8765-4321-876543218765"), note.id)


class TestRestoreNote:
    async def test_restore_note_success(self, service, repo):
        note = _make_note(deleted_at=datetime.now(timezone.utc))
        repo.get_by_id.return_value = note
        def _restore(n):
            n.deleted_at = None
            return n
        repo.restore.side_effect = _restore

        result = await service.restore_note(note.user_id, note.id)
        assert result.deleted_at is None
        repo.restore.assert_called_once_with(note)

    async def test_restore_note_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(NoteNotFoundException):
            await service.restore_note(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"))

    async def test_restore_note_already_active_raises(self, service, repo):
        note = _make_note(deleted_at=None)
        repo.get_by_id.return_value = note
        with pytest.raises(NoteValidationError, match="already active"):
            await service.restore_note(note.user_id, note.id)

    async def test_restore_note_access_denied(self, service, repo):
        note = _make_note(user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"), deleted_at=datetime.now(timezone.utc))
        repo.get_by_id.return_value = note
        with pytest.raises(NoteAccessDeniedException):
            await service.restore_note(uuid.UUID("87654321-4321-8765-4321-876543218765"), note.id)


class TestToggleArchiveStatus:
    async def test_archive_note_success(self, service, repo):
        note = _make_note()
        repo.get_by_id.return_value = note
        repo.update.return_value = note

        result = await service.toggle_archive_status(note.user_id, note.id, archive=True)
        repo.update.assert_called_once_with(note, {"is_archived": True})

    async def test_unarchive_note_success(self, service, repo):
        note = _make_note()
        repo.get_by_id.return_value = note
        repo.update.return_value = note

        result = await service.toggle_archive_status(note.user_id, note.id, archive=False)
        repo.update.assert_called_once_with(note, {"is_archived": False})

    async def test_archive_note_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(NoteNotFoundException):
            await service.toggle_archive_status(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"), archive=True)


class TestTogglePinStatus:
    async def test_pin_note_success(self, service, repo):
        note = _make_note()
        repo.get_by_id.return_value = note
        repo.update.return_value = note

        result = await service.toggle_pin_status(note.user_id, note.id, pin=True)
        repo.update.assert_called_once_with(note, {"is_pinned": True})

    async def test_unpin_note_success(self, service, repo):
        note = _make_note()
        repo.get_by_id.return_value = note
        repo.update.return_value = note

        result = await service.toggle_pin_status(note.user_id, note.id, pin=False)
        repo.update.assert_called_once_with(note, {"is_pinned": False})

    async def test_pin_note_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(NoteNotFoundException):
            await service.toggle_pin_status(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"), pin=True)


class TestToggleFavoriteStatus:
    async def test_favorite_note_success(self, service, repo):
        note = _make_note()
        repo.get_by_id.return_value = note
        repo.update.return_value = note

        result = await service.toggle_favorite_status(note.user_id, note.id, favorite=True)
        repo.update.assert_called_once_with(note, {"is_favorite": True})

    async def test_unfavorite_note_success(self, service, repo):
        note = _make_note()
        repo.get_by_id.return_value = note
        repo.update.return_value = note

        result = await service.toggle_favorite_status(note.user_id, note.id, favorite=False)
        repo.update.assert_called_once_with(note, {"is_favorite": False})

    async def test_favorite_note_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(NoteNotFoundException):
            await service.toggle_favorite_status(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"), favorite=True)


class TestGetAnalytics:
    async def test_get_analytics_delegates_to_repo(self, service, repo):
        repo.get_analytics.return_value = {"total": 5}
        result = await service.get_analytics(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert result["total"] == 5
        repo.get_analytics.assert_called_once()


class TestListAndFilterNotes:
    async def test_list_defaults_to_not_deleted(self, service, repo):
        repo.list_and_filter.return_value = []
        result = await service.list_and_filter_notes(uuid.UUID("87654321-4321-8765-4321-876543218765"))
        repo.list_and_filter.assert_called_once_with(
            user_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            search=None,
            category=None,
            tag=None,
            favorite=None,
            pinned=None,
            archived=False,
            deleted=False,
            sort_by="updated_at",
            sort_order="desc",
        )

    async def test_list_with_filters(self, service, repo):
        repo.list_and_filter.return_value = []
        await service.list_and_filter_notes(
            user_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            search="meeting",
            category="work",
            tag="urgent",
            favorite=True,
            pinned=False,
            archived=False,
            deleted=False,
            sort_by="created_at",
            sort_order="asc",
        )
        repo.list_and_filter.assert_called_once()

    async def test_list_invalid_sort_falls_back_to_updated_at(self, service, repo):
        repo.list_and_filter.return_value = []
        await service.list_and_filter_notes(
            user_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            sort_by="malicious_column",
        )
        call_kwargs = repo.list_and_filter.call_args[1]
        assert call_kwargs["sort_by"] == "updated_at"

    async def test_list_cases_insensitive_sort_order(self, service, repo):
        repo.list_and_filter.return_value = []
        await service.list_and_filter_notes(
            user_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            sort_order="ASC",
        )
        call_kwargs = repo.list_and_filter.call_args[1]
        assert call_kwargs["sort_order"] == "ASC"
