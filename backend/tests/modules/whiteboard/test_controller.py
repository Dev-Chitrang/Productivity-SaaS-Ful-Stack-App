import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
from fastapi import HTTPException, status
from app.modules.whiteboard.service import WhiteboardService
from app.modules.whiteboard.controller import WhiteboardController
from app.modules.whiteboard.schemas import (
    WhiteboardCreate,
    WhiteboardRename,
    WhiteboardAutosave,
    WhiteboardResponse,
    WhiteboardFilters,
)
from app.modules.whiteboard.exceptions import (
    WhiteboardNotFoundException,
    WhiteboardAccessDeniedException,
    WhiteboardValidationError,
)


class TestWhiteboardController:
    @pytest.fixture
    def controller(self):
        service = MagicMock(spec=WhiteboardService)
        return WhiteboardController(service)

    def _make_board_response(self, **kwargs):
        now = datetime.now(timezone.utc)
        return WhiteboardResponse(
            id=kwargs.get("id", uuid.UUID("12345678-1234-5678-1234-567812345678")),
            user_id=kwargs.get("user_id", uuid.UUID("87654321-4321-8765-4321-876543218765")),
            title=kwargs.get("title", "Test Board"),
            board_data=kwargs.get("board_data", {"version": 1, "elements": []}),
            is_favorite=kwargs.get("is_favorite", False),
            is_archived=kwargs.get("is_archived", False),
            is_deleted=kwargs.get("is_deleted", False),
            created_at=now,
            updated_at=now,
            deleted_at=kwargs.get("deleted_at", None),
        )

    async def test_create_board_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        mock_board = self._make_board_response()
        controller.service.create_board.return_value = mock_board

        payload = WhiteboardCreate(title="New Board")
        result = await controller.create_board(user_id, payload)
        assert result.model_dump()["title"] == "Test Board"
        controller.service.create_board.assert_called_once_with(user_id, payload)

    async def test_get_board_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_board = self._make_board_response()
        controller.service.get_board.return_value = mock_board

        result = await controller.get_board(user_id, board_id)
        assert result.model_dump()["id"] == board_id
        controller.service.get_board.assert_called_once_with(user_id, board_id)

    async def test_get_board_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.get_board.side_effect = WhiteboardNotFoundException(board_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.get_board(user_id, board_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_board_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.get_board.side_effect = WhiteboardAccessDeniedException(board_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.get_board(user_id, board_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_get_board_validation_error(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.get_board.side_effect = WhiteboardValidationError("soft-deleted")
        with pytest.raises(HTTPException) as exc_info:
            await controller.get_board(user_id, board_id)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_rename_board_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_board = self._make_board_response(title="Renamed")
        controller.service.rename_board.return_value = mock_board

        payload = WhiteboardRename(title="Renamed")
        result = await controller.rename_board(user_id, board_id, payload)
        assert result.model_dump()["title"] == "Renamed"
        controller.service.rename_board.assert_called_once_with(user_id, board_id, payload)

    async def test_rename_board_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.rename_board.side_effect = WhiteboardNotFoundException(board_id)
        payload = WhiteboardRename(title="Renamed")
        with pytest.raises(HTTPException) as exc_info:
            await controller.rename_board(user_id, board_id, payload)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_rename_board_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.rename_board.side_effect = WhiteboardAccessDeniedException(board_id, user_id)
        payload = WhiteboardRename(title="Renamed")
        with pytest.raises(HTTPException) as exc_info:
            await controller.rename_board(user_id, board_id, payload)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_rename_board_validation_error(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.rename_board.side_effect = WhiteboardValidationError("invalid")
        payload = WhiteboardRename(title="Renamed")
        with pytest.raises(HTTPException) as exc_info:
            await controller.rename_board(user_id, board_id, payload)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_autosave_board_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_board = self._make_board_response()
        controller.service.update_board_payload.return_value = mock_board

        payload = WhiteboardAutosave(board_data={"version": 2, "elements": []})
        result = await controller.autosave_board(user_id, board_id, payload)
        assert result.model_dump()["id"] == board_id
        controller.service.update_board_payload.assert_called_once_with(user_id, board_id, payload)

    async def test_autosave_board_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.update_board_payload.side_effect = WhiteboardNotFoundException(board_id)
        payload = WhiteboardAutosave(board_data={"version": 2})
        with pytest.raises(HTTPException) as exc_info:
            await controller.autosave_board(user_id, board_id, payload)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_autosave_board_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.update_board_payload.side_effect = WhiteboardAccessDeniedException(board_id, user_id)
        payload = WhiteboardAutosave(board_data={"version": 2})
        with pytest.raises(HTTPException) as exc_info:
            await controller.autosave_board(user_id, board_id, payload)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_set_favorite_status_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_board = self._make_board_response()
        controller.service.toggle_favorite.return_value = mock_board

        result = await controller.set_favorite_status(user_id, board_id, True)
        controller.service.toggle_favorite.assert_called_once_with(user_id, board_id, True)

    async def test_set_favorite_status_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_favorite.side_effect = WhiteboardNotFoundException(board_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.set_favorite_status(user_id, board_id, True)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_set_favorite_status_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_favorite.side_effect = WhiteboardAccessDeniedException(board_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.set_favorite_status(user_id, board_id, True)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_set_archive_status_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_board = self._make_board_response()
        controller.service.toggle_archive.return_value = mock_board

        result = await controller.set_archive_status(user_id, board_id, True)
        controller.service.toggle_archive.assert_called_once_with(user_id, board_id, True)

    async def test_set_archive_status_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_archive.side_effect = WhiteboardNotFoundException(board_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.set_archive_status(user_id, board_id, True)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_set_archive_status_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.toggle_archive.side_effect = WhiteboardAccessDeniedException(board_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.set_archive_status(user_id, board_id, True)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_delete_board_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.soft_delete_board.return_value = None

        result = await controller.delete_board(user_id, board_id)
        assert result["status"] == "success"
        assert "soft-deleted" in result["message"]

    async def test_delete_board_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.soft_delete_board.side_effect = WhiteboardNotFoundException(board_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.delete_board(user_id, board_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_board_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.soft_delete_board.side_effect = WhiteboardAccessDeniedException(board_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.delete_board(user_id, board_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_restore_board_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_board = self._make_board_response()
        controller.service.restore_board.return_value = mock_board

        result = await controller.restore_board(user_id, board_id)
        assert result.model_dump()["id"] == board_id
        controller.service.restore_board.assert_called_once_with(user_id, board_id)

    async def test_restore_board_not_found(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.restore_board.side_effect = WhiteboardNotFoundException(board_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.restore_board(user_id, board_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_restore_board_access_denied(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.restore_board.side_effect = WhiteboardAccessDeniedException(board_id, user_id)
        with pytest.raises(HTTPException) as exc_info:
            await controller.restore_board(user_id, board_id)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_restore_board_already_active(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        controller.service.restore_board.side_effect = WhiteboardValidationError("already active")
        with pytest.raises(HTTPException) as exc_info:
            await controller.restore_board(user_id, board_id)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    async def test_list_boards_success(self, controller):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        mock_board = self._make_board_response()
        controller.service.list_user_boards.return_value = [mock_board]

        filters = WhiteboardFilters(is_archived=False, is_deleted=False)
        result = await controller.list_boards(user_id, filters)
        assert len(result) == 1
        assert result[0].model_dump()["title"] == "Test Board"
