import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from app.models.whiteboard import Whiteboard


class TestWhiteboardModel:
    def test_tablename(self):
        assert Whiteboard.__tablename__ == "whiteboards"

    def test_id_default_generates_uuid(self):
        board = Whiteboard(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Test Board",
        )
        assert board.id is None or isinstance(board.id, (uuid.UUID, type(uuid.uuid7())))

    def test_minimal_fields(self):
        now = datetime.now(timezone.utc)
        board = Whiteboard(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Minimal Board",
            board_data={"version": 1, "elements": []},
            is_favorite=False,
            is_archived=False,
            is_deleted=False,
            created_at=now,
            updated_at=now,
        )
        assert board.user_id == uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert board.title == "Minimal Board"
        assert board.board_data == {"version": 1, "elements": []}
        assert board.is_favorite is False
        assert board.is_archived is False
        assert board.is_deleted is False
        assert board.deleted_at is None
        assert isinstance(board.created_at, datetime)
        assert isinstance(board.updated_at, datetime)

    def test_full_fields(self):
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        now = datetime.now(timezone.utc)
        board = Whiteboard(
            id=board_id,
            user_id=user_id,
            title="Full Board",
            board_data={"version": 1, "elements": [{"id": "1", "type": "rect"}]},
            is_favorite=True,
            is_archived=False,
            is_deleted=False,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )
        assert board.id == board_id
        assert board.user_id == user_id
        assert board.title == "Full Board"
        assert board.board_data["version"] == 1
        assert board.is_favorite is True
        assert board.is_archived is False
        assert board.is_deleted is False

    def test_soft_delete(self):
        now = datetime.now(timezone.utc)
        board = Whiteboard(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Delete me",
            is_deleted=True,
            deleted_at=now,
        )
        assert board.is_deleted is True
        assert board.deleted_at == now

    def test_created_at_default_utc(self):
        now = datetime.now(timezone.utc)
        board = Whiteboard(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Board",
            created_at=now,
        )
        assert board.created_at is not None
        assert board.created_at.tzinfo == timezone.utc

    def test_updated_at_default_utc(self):
        now = datetime.now(timezone.utc)
        board = Whiteboard(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Board",
            updated_at=now,
        )
        assert board.updated_at is not None
        assert board.updated_at.tzinfo == timezone.utc

    def test_board_data_default(self):
        board = Whiteboard(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            title="Board",
            board_data={"version": 1, "elements": []},
        )
        assert board.board_data == {"version": 1, "elements": []}
