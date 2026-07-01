from typing import Sequence
from uuid import UUID
from datetime import datetime, timezone

from app.modules.whiteboard.repository import WhiteboardRepository
from app.models.whiteboard import Whiteboard
from app.modules.whiteboard.schemas import WhiteboardCreate, WhiteboardRename, WhiteboardAutosave, WhiteboardFilters
from app.modules.whiteboard.exceptions import WhiteboardNotFoundException, WhiteboardAccessDeniedException, WhiteboardValidationError

class WhiteboardService:
    def __init__(self, repo: WhiteboardRepository, activity_service=None):
        self.repo = repo
        self.activity_service = activity_service # Injected system logging wrapper if present

    async def _log_activity(self, user_id: UUID, board_id: UUID, action: str, details: dict):
        """Dispatches event states to the centralized activity stream if integrated."""
        if self.activity_service and hasattr(self.activity_service, "log_event"):
            await self.activity_service.log_event(
                user_id=user_id, module="WHITEBOARD", target_id=board_id, action=action, details=details
            )

    async def get_board(self, user_id: UUID, board_id: UUID, allow_deleted: bool = False) -> Whiteboard:
        board = await self.repo.get_by_id(board_id)
        if not board:
            raise WhiteboardNotFoundException(board_id)
        if board.user_id != user_id:
            raise WhiteboardAccessDeniedException(board_id, user_id)
        if board.is_deleted and not allow_deleted:
            raise WhiteboardValidationError("Cannot access a soft-deleted board asset wrapper.")
        return board

    async def create_board(self, user_id: UUID, payload: WhiteboardCreate) -> Whiteboard:
        board = await self.repo.create(user_id, payload.model_dump())
        await self._log_activity(user_id, board.id, "BOARD_CREATED", {"title": board.title})
        return board

    async def update_board_payload(self, user_id: UUID, board_id: UUID, payload: WhiteboardAutosave) -> Whiteboard:
        """Saves incoming drawing canvas primitives frequently. Intentionally skips audit logs."""
        board = await self.get_board(user_id, board_id)
        return await self.repo.update(board, {"board_data": payload.board_data})

    async def rename_board(self, user_id: UUID, board_id: UUID, payload: WhiteboardRename) -> Whiteboard:
        board = await self.get_board(user_id, board_id)
        old_title = board.title
        updated_board = await self.repo.update(board, {"title": payload.title})
        await self._log_activity(user_id, board_id, "BOARD_RENAMED", {"old_title": old_title, "new_title": payload.title})
        return updated_board

    async def toggle_favorite(self, user_id: UUID, board_id: UUID, is_fav: bool) -> Whiteboard:
        board = await self.get_board(user_id, board_id)
        return await self.repo.update(board, {"is_favorite": is_fav})

    async def toggle_archive(self, user_id: UUID, board_id: UUID, archive: bool) -> Whiteboard:
        board = await self.get_board(user_id, board_id)
        updated_board = await self.repo.update(board, {"is_archived": archive})
        action = "BOARD_ARCHIVED" if archive else "BOARD_UNARCHIVED"
        await self._log_activity(user_id, board_id, action, {"title": board.title})
        return updated_board

    async def soft_delete_board(self, user_id: UUID, board_id: UUID) -> None:
        board = await self.get_board(user_id, board_id)
        await self.repo.update(board, {
            "is_deleted": True,
            "deleted_at": datetime.now(timezone.utc)
        })
        await self._log_activity(user_id, board_id, "BOARD_DELETED", {"title": board.title})

    async def restore_board(self, user_id: UUID, board_id: UUID) -> Whiteboard:
        board = await self.get_board(user_id, board_id, allow_deleted=True)
        if not board.is_deleted:
            raise WhiteboardValidationError("Whiteboard asset context is already active.")

        updated_board = await self.repo.update(board, {
            "is_deleted": False,
            "deleted_at": None
        })
        await self._log_activity(user_id, board_id, "BOARD_RESTORED", {"title": board.title})
        return updated_board

    async def list_user_boards(self, user_id: UUID, filters: WhiteboardFilters) -> Sequence[Whiteboard]:
        return await self.repo.list_boards(user_id, filters)
