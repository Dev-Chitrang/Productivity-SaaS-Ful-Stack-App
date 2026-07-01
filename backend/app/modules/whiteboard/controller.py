from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status

from app.modules.whiteboard.service import WhiteboardService
from app.modules.whiteboard.schemas import (
    WhiteboardCreate, WhiteboardRename, WhiteboardAutosave,
    WhiteboardResponse, WhiteboardFilters
)
from app.modules.whiteboard.exceptions import (
    WhiteboardNotFoundException, WhiteboardAccessDeniedException, WhiteboardValidationError
)

class WhiteboardController:
    def __init__(self, service: WhiteboardService):
        self.service = service

    async def create_board(self, user_id: UUID, payload: WhiteboardCreate) -> dict:
        board = await self.service.create_board(user_id, payload)
        return WhiteboardResponse.model_validate(board)

    async def get_board(self, user_id: UUID, board_id: UUID) -> dict:
        try:
            board = await self.service.get_board(user_id, board_id)
            return WhiteboardResponse.model_validate(board)
        except WhiteboardNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except WhiteboardAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except WhiteboardValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def rename_board(self, user_id: UUID, board_id: UUID, payload: WhiteboardRename) -> dict:
        try:
            board = await self.service.rename_board(user_id, board_id, payload)
            return WhiteboardResponse.model_validate(board)
        except WhiteboardNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except WhiteboardAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except WhiteboardValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def autosave_board(self, user_id: UUID, board_id: UUID, payload: WhiteboardAutosave) -> dict:
        try:
            board = await self.service.update_board_payload(user_id, board_id, payload)
            return WhiteboardResponse.model_validate(board)
        except WhiteboardNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except WhiteboardAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def set_favorite_status(self, user_id: UUID, board_id: UUID, is_fav: bool) -> dict:
        try:
            board = await self.service.toggle_favorite(user_id, board_id, is_fav)
            return WhiteboardResponse.model_validate(board)
        except WhiteboardNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except WhiteboardAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def set_archive_status(self, user_id: UUID, board_id: UUID, archive: bool) -> dict:
        try:
            board = await self.service.toggle_archive(user_id, board_id, archive)
            return WhiteboardResponse.model_validate(board)
        except WhiteboardNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except WhiteboardAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def delete_board(self, user_id: UUID, board_id: UUID) -> dict:
        try:
            await self.service.soft_delete_board(user_id, board_id)
            return {"status": "success", "message": "Whiteboard session safely soft-deleted."}
        except WhiteboardNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except WhiteboardAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def restore_board(self, user_id: UUID, board_id: UUID) -> dict:
        try:
            board = await self.service.restore_board(user_id, board_id)
            return WhiteboardResponse.model_validate(board)
        except WhiteboardNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except WhiteboardAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except WhiteboardValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def list_boards(self, user_id: UUID, filters: WhiteboardFilters) -> List[dict]:
        boards = await self.service.list_user_boards(user_id, filters)
        return [WhiteboardResponse.model_validate(b) for b in boards]
