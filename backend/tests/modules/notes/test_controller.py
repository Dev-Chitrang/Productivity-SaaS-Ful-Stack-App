import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
import pytest
from fastapi import HTTPException, status
from app.modules.notes.services import NoteService
from app.modules.notes.controller import NoteController
from app.modules.notes.schemas import NoteCreate, NoteUpdate, NoteResponse, NoteListResponse
from app.modules.notes.exceptions import (
    NoteNotFoundException,
    NoteAccessDeniedException,
    NoteValidationError,
)


class TestNoteController:
    @pytest.fixture
    def controller(self):
        service = MagicMock(spec=NoteService)
        return NoteController(service)

    def _make_note_response(self, **kwargs):
        now = datetime.now(timezone.utc)
        return NoteResponse(
            id=kwargs.get("id", uuid.UUID("12345678-1234-5678-1234-567812345678")),
            user_id=kwargs.get("user_id", uuid.UUID("87654321-4321-8765-4321-876543218765")),
            title=kwargs.get("title", "Test Note"),
            content=kwargs.get("content", "Content here"),
            category=kwargs.get("category", "personal"),
            tags=kwargs.get("tags", []),
            is_pinned=kwargs.get("is_pinned", False),
            is_favorite=kwargs.get("is_favorite", False),
            is_archived=kwargs.get("is_archived", False),
            created_at=now,
            updated_at=now,
            deleted_at=kwargs.get("deleted_at", None),
        )

    async def test_create_user_note_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        mock_note = self._make_note_response()
        controller.service.create_note.return_value = mock_note

        payload = NoteCreate(title="New Note", content="Content")
        result = await controller.create_user_note(user_id, payload)
        assert result.title == "Test Note"
        controller.service.create_note.assert_called_once_with(user_id, payload)

    async def test_create_user_note_validation_error(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        controller.service.create_note.side_effect = NoteValidationError("Empty note")
        payload = NoteCreate(title="valid", content="valid")
        with pytest.raises(HTTPException) as exc_info:
            await controller.create_user_note(user_id, payload)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_get_user_note_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_note = self._make_note_response()
        controller.service.get_note.return_value = mock_note

        result = await controller.get_user_note(user_id, note_id)
        assert result.id == note_id
        controller.service.get_note.assert_called_once_with(user_id, note_id, include_deleted=True)

    async def test_get_user_note_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.get_note.side_effect = NoteNotFoundException(note_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.get_user_note(user_id, note_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_user_note_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.get_note.side_effect = NoteAccessDeniedException(note_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.get_user_note(user_id, note_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_update_user_note_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_note = self._make_note_response(title="Updated")
        controller.service.update_note.return_value = mock_note

        payload = NoteUpdate(title="Updated")
        result = await controller.update_user_note(user_id, note_id, payload)
        assert result.title == "Updated"
        controller.service.update_note.assert_called_once_with(user_id, note_id, payload)

    async def test_update_user_note_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.update_note.side_effect = NoteNotFoundException(note_id)
        payload = NoteUpdate(title="Updated")
        with pytest.raises(HTTPException) as exc_info:
            await controller.update_user_note(user_id, note_id, payload)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_user_note_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.update_note.side_effect = NoteAccessDeniedException(note_id, user_id)
        payload = NoteUpdate(title="Updated")
        with pytest.raises(HTTPException) as exc_info:
            await controller.update_user_note(user_id, note_id, payload)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_update_user_note_validation_error(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.update_note.side_effect = NoteValidationError("Cannot strip")
        payload = NoteUpdate(title="valid", content="valid")
        with pytest.raises(HTTPException) as exc_info:
            await controller.update_user_note(user_id, note_id, payload)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_delete_user_note_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.delete_note.return_value = None

        result = await controller.delete_user_note(user_id, note_id)
        assert result["status"] == "success"
        assert "trash" in result["message"]
        controller.service.delete_note.assert_called_once_with(user_id, note_id)

    async def test_delete_user_note_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.delete_note.side_effect = NoteNotFoundException(note_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.delete_user_note(user_id, note_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_user_note_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.delete_note.side_effect = NoteAccessDeniedException(note_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.delete_user_note(user_id, note_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_restore_user_note_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_note = self._make_note_response()
        controller.service.restore_note.return_value = mock_note

        result = await controller.restore_user_note(user_id, note_id)
        assert result.id == note_id
        controller.service.restore_note.assert_called_once_with(user_id, note_id)

    async def test_restore_user_note_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.restore_note.side_effect = NoteNotFoundException(note_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.restore_user_note(user_id, note_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_restore_user_note_already_active(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.restore_note.side_effect = NoteValidationError("already active")
        with pytest.raises(HTTPException) as exc_info:
            await controller.restore_user_note(user_id, note_id)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_archive_user_note_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_note = self._make_note_response()
        controller.service.toggle_archive_status.return_value = mock_note

        result = await controller.archive_user_note(user_id, note_id)
        assert result.is_archived is False
        controller.service.toggle_archive_status.assert_called_once_with(user_id, note_id, archive=True)

    async def test_archive_user_note_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_archive_status.side_effect = NoteNotFoundException(note_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.archive_user_note(user_id, note_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_archive_user_note_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_archive_status.side_effect = NoteAccessDeniedException(note_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.archive_user_note(user_id, note_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_unarchive_user_note_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_note = self._make_note_response()
        controller.service.toggle_archive_status.return_value = mock_note

        result = await controller.unarchive_user_note(user_id, note_id)
        controller.service.toggle_archive_status.assert_called_once_with(user_id, note_id, archive=False)

    async def test_unarchive_user_note_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_archive_status.side_effect = NoteNotFoundException(note_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.unarchive_user_note(user_id, note_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_unarchive_user_note_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_archive_status.side_effect = NoteAccessDeniedException(note_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.unarchive_user_note(user_id, note_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_pin_user_note_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_note = self._make_note_response()
        controller.service.toggle_pin_status.return_value = mock_note

        result = await controller.pin_user_note(user_id, note_id)
        controller.service.toggle_pin_status.assert_called_once_with(user_id, note_id, pin=True)

    async def test_pin_user_note_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_pin_status.side_effect = NoteNotFoundException(note_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.pin_user_note(user_id, note_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_pin_user_note_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_pin_status.side_effect = NoteAccessDeniedException(note_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.pin_user_note(user_id, note_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_unpin_user_note_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_note = self._make_note_response()
        controller.service.toggle_pin_status.return_value = mock_note

        result = await controller.unpin_user_note(user_id, note_id)
        controller.service.toggle_pin_status.assert_called_once_with(user_id, note_id, pin=False)

    async def test_unpin_user_note_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_pin_status.side_effect = NoteNotFoundException(note_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.unpin_user_note(user_id, note_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_unpin_user_note_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_pin_status.side_effect = NoteAccessDeniedException(note_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.unpin_user_note(user_id, note_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_favorite_user_note_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_note = self._make_note_response()
        controller.service.toggle_favorite_status.return_value = mock_note

        result = await controller.favorite_user_note(user_id, note_id)
        controller.service.toggle_favorite_status.assert_called_once_with(user_id, note_id, favorite=True)

    async def test_favorite_user_note_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_favorite_status.side_effect = NoteNotFoundException(note_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.favorite_user_note(user_id, note_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_favorite_user_note_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_favorite_status.side_effect = NoteAccessDeniedException(note_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.favorite_user_note(user_id, note_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_unfavorite_user_note_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_note = self._make_note_response()
        controller.service.toggle_favorite_status.return_value = mock_note

        result = await controller.unfavorite_user_note(user_id, note_id)
        controller.service.toggle_favorite_status.assert_called_once_with(user_id, note_id, favorite=False)

    async def test_unfavorite_user_note_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_favorite_status.side_effect = NoteNotFoundException(note_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.unfavorite_user_note(user_id, note_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_unfavorite_user_note_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_favorite_status.side_effect = NoteAccessDeniedException(note_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.unfavorite_user_note(user_id, note_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_get_analytics_delegates(self, controller):
        controller.service.get_analytics.return_value = {"total": 5}
        result = await controller.get_analytics(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert result["total"] == 5

    async def test_list_user_notes_returns_list_response(self, controller):
        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_note = self._make_note_response()
        controller.service.list_and_filter_notes.return_value = [mock_note]

        result = await controller.list_user_notes(
            user_id=user_id,
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
        assert result.total_count == 1
        assert len(result.notes) == 1
        assert result.notes[0].title == "Test Note"
