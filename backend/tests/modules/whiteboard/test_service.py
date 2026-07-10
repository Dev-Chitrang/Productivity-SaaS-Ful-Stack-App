import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.modules.whiteboard.exceptions import (
    WhiteboardNotFoundException,
    WhiteboardAccessDeniedException,
    WhiteboardValidationError,
)
from app.modules.whiteboard.repository import WhiteboardRepository
from app.modules.whiteboard.service import WhiteboardService
from app.modules.whiteboard.schemas import WhiteboardCreate, WhiteboardRename, WhiteboardAutosave, WhiteboardFilters
from app.models.whiteboard import Whiteboard


@pytest.fixture
def repo():
    return MagicMock(spec=WhiteboardRepository)


@pytest.fixture
def service(repo):
    return WhiteboardService(repo, activity_service=None)


def _make_board(**kwargs):
    now = datetime.now(timezone.utc)
    return Whiteboard(
        id=kwargs.get("id", uuid.UUID("12345678-1234-5678-1234-567812345678")),
        user_id=kwargs.get("user_id", uuid.UUID("87654321-4321-8765-4321-876543218765")),
        title=kwargs.get("title", "Test Board"),
        board_data=kwargs.get("board_data", {"version": 1, "elements": []}),
        is_favorite=kwargs.get("is_favorite", False),
        is_archived=kwargs.get("is_archived", False),
        is_deleted=kwargs.get("is_deleted", False),
        deleted_at=kwargs.get("deleted_at", None),
        created_at=kwargs.get("created_at", now),
        updated_at=kwargs.get("updated_at", now),
    )


class TestGetBoard:
    async def test_get_board_success(self, service, repo):
        board = _make_board()
        repo.get_by_id.return_value = board

        result = await service.get_board(board.user_id, board.id)
        assert result == board
        repo.get_by_id.assert_called_once_with(board.id)

    async def test_get_board_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(WhiteboardNotFoundException):
            await service.get_board(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"))

    async def test_get_board_access_denied(self, service, repo):
        board = _make_board(user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"))
        repo.get_by_id.return_value = board
        with pytest.raises(WhiteboardAccessDeniedException):
            await service.get_board(uuid.UUID("87654321-4321-8765-4321-876543218765"), board.id)

    async def test_get_board_deleted_not_allowed(self, service, repo):
        board = _make_board(is_deleted=True, deleted_at=datetime.now(timezone.utc))
        repo.get_by_id.return_value = board
        with pytest.raises(WhiteboardValidationError, match="soft-deleted"):
            await service.get_board(board.user_id, board.id)

    async def test_get_board_deleted_allowed_when_flag_true(self, service, repo):
        board = _make_board(is_deleted=True, deleted_at=datetime.now(timezone.utc))
        repo.get_by_id.return_value = board
        result = await service.get_board(board.user_id, board.id, allow_deleted=True)
        assert result == board


class TestCreateBoard:
    async def test_create_board_success(self, service, repo):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        payload = WhiteboardCreate(title="New Board")
        repo.create.return_value = _make_board()

        result = await service.create_board(user_id, payload)
        repo.create.assert_called_once_with(user_id, payload.model_dump())

    async def test_create_board_logs_activity(self, service, repo):
        activity_service = AsyncMock()
        service_with_log = WhiteboardService(repo, activity_service=activity_service)
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        payload = WhiteboardCreate(title="New Board")
        repo.create.return_value = _make_board()

        await service_with_log.create_board(user_id, payload)
        activity_service.log_event.assert_called_once()


class TestUpdateBoardPayload:
    async def test_update_board_payload_success(self, service, repo):
        board = _make_board()
        repo.get_by_id.return_value = board
        repo.update.return_value = board

        payload = WhiteboardAutosave(board_data={"version": 2, "elements": [{"id": "1"}]})
        result = await service.update_board_payload(board.user_id, board.id, payload)
        repo.update.assert_called_once_with(board, {"board_data": payload.board_data})

    async def test_update_board_payload_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        payload = WhiteboardAutosave(board_data={"version": 2})
        with pytest.raises(WhiteboardNotFoundException):
            await service.update_board_payload(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"), payload)

    async def test_update_board_payload_access_denied(self, service, repo):
        board = _make_board(user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"))
        repo.get_by_id.return_value = board
        payload = WhiteboardAutosave(board_data={"version": 2})
        with pytest.raises(WhiteboardAccessDeniedException):
            await service.update_board_payload(uuid.UUID("87654321-4321-8765-4321-876543218765"), board.id, payload)


class TestRenameBoard:
    async def test_rename_board_success(self, service, repo):
        board = _make_board()
        repo.get_by_id.return_value = board
        repo.update.return_value = board

        payload = WhiteboardRename(title="Renamed")
        result = await service.rename_board(board.user_id, board.id, payload)
        repo.update.assert_called_once_with(board, {"title": "Renamed"})

    async def test_rename_board_logs_activity(self, service, repo):
        activity_service = AsyncMock()
        service_with_log = WhiteboardService(repo, activity_service=activity_service)
        board = _make_board()
        repo.get_by_id.return_value = board
        repo.update.return_value = board

        payload = WhiteboardRename(title="Renamed")
        await service_with_log.rename_board(board.user_id, board.id, payload)
        activity_service.log_event.assert_called_once()


class TestToggleFavorite:
    async def test_toggle_favorite_success(self, service, repo):
        board = _make_board()
        repo.get_by_id.return_value = board
        repo.update.return_value = board

        result = await service.toggle_favorite(board.user_id, board.id, True)
        repo.update.assert_called_once_with(board, {"is_favorite": True})

    async def test_toggle_unfavorite_success(self, service, repo):
        board = _make_board(is_favorite=True)
        repo.get_by_id.return_value = board
        repo.update.return_value = board

        result = await service.toggle_favorite(board.user_id, board.id, False)
        repo.update.assert_called_once_with(board, {"is_favorite": False})

    async def test_toggle_favorite_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(WhiteboardNotFoundException):
            await service.toggle_favorite(uuid.UUID("87654321-4321-8765-4321-876543218765"), uuid.UUID("12345678-1234-5678-1234-567812345678"), True)


class TestToggleArchive:
    async def test_archive_board_success(self, service, repo):
        board = _make_board()
        repo.get_by_id.return_value = board
        repo.update.return_value = board

        result = await service.toggle_archive(board.user_id, board.id, True)
        repo.update.assert_called_once_with(board, {"is_archived": True})

    async def test_unarchive_board_success(self, service, repo):
        board = _make_board(is_archived=True)
        repo.get_by_id.return_value = board
        repo.update.return_value = board

        result = await service.toggle_archive(board.user_id, board.id, False)
        repo.update.assert_called_once_with(board, {"is_archived": False})

    async def test_archive_board_logs_activity(self, service, repo):
        activity_service = AsyncMock()
        service_with_log = WhiteboardService(repo, activity_service=activity_service)
        board = _make_board()
        repo.get_by_id.return_value = board
        repo.update.return_value = board

        await service_with_log.toggle_archive(board.user_id, board.id, True)
        activity_service.log_event.assert_called_once()


class TestSoftDeleteBoard:
    async def test_soft_delete_board_success(self, service, repo):
        board = _make_board(is_deleted=False)
        repo.get_by_id.return_value = board
        repo.update.return_value = board

        await service.soft_delete_board(board.user_id, board.id)
        repo.update.assert_called_once()
        update_data = repo.update.call_args[0][1]
        assert update_data["is_deleted"] is True
        assert "deleted_at" in update_data

    async def test_soft_delete_board_logs_activity(self, service, repo):
        activity_service = AsyncMock()
        service_with_log = WhiteboardService(repo, activity_service=activity_service)
        board = _make_board()
        repo.get_by_id.return_value = board
        repo.update.return_value = board

        await service_with_log.soft_delete_board(board.user_id, board.id)
        activity_service.log_event.assert_called_once()


class TestRestoreBoard:
    async def test_restore_board_success(self, service, repo):
        board = _make_board(is_deleted=True, deleted_at=datetime.now(timezone.utc))
        repo.get_by_id.return_value = board

        def _apply_update(b, data):
            for key, value in data.items():
                setattr(b, key, value)
            return b
        repo.update.side_effect = _apply_update

        result = await service.restore_board(board.user_id, board.id)
        assert result.is_deleted is False
        assert result.deleted_at is None

    async def test_restore_board_already_active_raises(self, service, repo):
        board = _make_board(is_deleted=False)
        repo.get_by_id.return_value = board
        with pytest.raises(WhiteboardValidationError, match="already active"):
            await service.restore_board(board.user_id, board.id)

    async def test_restore_board_logs_activity(self, service, repo):
        activity_service = AsyncMock()
        service_with_log = WhiteboardService(repo, activity_service=activity_service)
        board = _make_board(is_deleted=True, deleted_at=datetime.now(timezone.utc))
        repo.get_by_id.return_value = board
        repo.update.return_value = board

        await service_with_log.restore_board(board.user_id, board.id)
        activity_service.log_event.assert_called_once()


class TestListUserBoards:
    async def test_list_user_boards_delegates_to_repo(self, service, repo):
        repo.list_boards.return_value = []
        filters = WhiteboardFilters(is_archived=False, is_deleted=False)
        result = await service.list_user_boards(uuid.UUID("87654321-4321-8765-4321-876543218765"), filters)
        repo.list_boards.assert_called_once_with(uuid.UUID("87654321-4321-8765-4321-876543218765"), filters)
