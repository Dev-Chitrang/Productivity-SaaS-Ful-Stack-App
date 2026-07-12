import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.whiteboard.repository import WhiteboardRepository
from app.models.whiteboard import Whiteboard
from app.modules.whiteboard.schemas import WhiteboardFilters


@pytest.fixture
def repo():
    db = AsyncMock(spec=AsyncSession)
    return WhiteboardRepository(db)


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


class TestWhiteboardRepositoryCreate:
    async def test_create_success(self, repo):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_data = {"title": "New Board", "board_data": {"version": 1, "elements": []}}
        result = await repo.create(user_id, board_data)
        assert result.user_id == user_id
        assert result.title == "New Board"
        repo.db.add.assert_called_once()
        repo.db.flush.assert_called_once()

    async def test_create_default_board_data(self, repo):
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        board_data = {"title": "New Board", "board_data": {"version": 1, "elements": []}}
        result = await repo.create(user_id, board_data)
        assert result.board_data == {"version": 1, "elements": []}


class TestWhiteboardRepositoryGetById:
    async def test_get_by_id_found(self, repo):
        board = _make_board()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = board
        repo.db.execute.return_value = result_mock

        found = await repo.get_by_id(board.id)
        assert found == board

    async def test_get_by_id_not_found(self, repo):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        repo.db.execute.return_value = result_mock

        found = await repo.get_by_id(uuid.UUID("12345678-1234-5678-1234-567812345678"))
        assert found is None


class TestWhiteboardRepositoryUpdate:
    async def test_update_success(self, repo):
        board = _make_board()
        update_data = {"title": "Updated Board", "is_favorite": True}
        result = await repo.update(board, update_data)
        assert result.title == "Updated Board"
        assert result.is_favorite is True
        repo.db.add.assert_called_once_with(board)
        repo.db.flush.assert_called_once()

    async def test_update_partial_fields(self, repo):
        board = _make_board()
        update_data = {"title": "Updated Board"}
        result = await repo.update(board, update_data)
        assert result.title == "Updated Board"
        assert result.is_favorite is False


class TestWhiteboardRepositoryListBoards:
    async def test_list_boards_returns_sequence(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        filters = WhiteboardFilters(is_archived=False, is_deleted=False)
        result = await repo.list_boards(uuid.UUID("87654321-4321-8765-4321-876543218765"), filters)
        assert isinstance(result, list)

    async def test_list_boards_filters_by_user(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        filters = WhiteboardFilters(is_archived=False, is_deleted=False)
        await repo.list_boards(uuid.UUID("87654321-4321-8765-4321-876543218765"), filters)
        stmt = repo.db.execute.call_args[0][0]
        assert "user_id" in str(stmt)

    async def test_list_boards_applies_archived_filter(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        filters = WhiteboardFilters(is_archived=True, is_deleted=False)
        await repo.list_boards(uuid.UUID("87654321-4321-8765-4321-876543218765"), filters)
        stmt = repo.db.execute.call_args[0][0]
        assert "is_archived" in str(stmt)

    async def test_list_boards_applies_deleted_filter(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        filters = WhiteboardFilters(is_archived=False, is_deleted=True)
        await repo.list_boards(uuid.UUID("87654321-4321-8765-4321-876543218765"), filters)
        stmt = repo.db.execute.call_args[0][0]
        assert "is_deleted" in str(stmt)

    async def test_list_boards_applies_favorite_filter(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        filters = WhiteboardFilters(is_archived=False, is_deleted=False, is_favorite=True)
        await repo.list_boards(uuid.UUID("87654321-4321-8765-4321-876543218765"), filters)
        stmt = repo.db.execute.call_args[0][0]
        assert "is_favorite" in str(stmt)

    async def test_list_boards_applies_search_filter(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        filters = WhiteboardFilters(is_archived=False, is_deleted=False, search="meeting")
        await repo.list_boards(uuid.UUID("87654321-4321-8765-4321-876543218765"), filters)
        stmt = repo.db.execute.call_args[0][0]
        compiled = stmt.compile(compile_kwargs={"literal_binds": True})
        assert "meeting" in str(compiled).lower()

    async def test_list_boards_orders_by_updated_at_desc(self, repo):
        repo.db.execute.return_value = MagicMock()
        repo.db.execute.return_value.scalars.return_value.all.return_value = []

        filters = WhiteboardFilters(is_archived=False, is_deleted=False)
        await repo.list_boards(uuid.UUID("87654321-4321-8765-4321-876543218765"), filters)
        stmt = repo.db.execute.call_args[0][0]
        assert "updated_at" in str(stmt)
        assert "desc" in str(stmt).lower()
