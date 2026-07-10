import pytest
from pydantic import ValidationError
from app.modules.whiteboard.schemas import (
    WhiteboardBase,
    WhiteboardCreate,
    WhiteboardRename,
    WhiteboardAutosave,
    WhiteboardResponse,
    WhiteboardFilters,
)
from uuid import UUID
from datetime import datetime


class TestWhiteboardBase:
    def test_valid_base(self):
        model = WhiteboardBase(title="My Whiteboard")
        assert model.title == "My Whiteboard"

    def test_title_strips_whitespace(self):
        model = WhiteboardBase(title="  My Whiteboard  ")
        assert model.title == "My Whiteboard"

    def test_empty_title_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            WhiteboardBase(title="   ")

    def test_title_max_length(self):
        title = "a" * 255
        model = WhiteboardBase(title=title)
        assert len(model.title) == 255

    def test_title_exceeds_max_length(self):
        title = "a" * 256
        with pytest.raises(ValidationError):
            WhiteboardBase(title=title)


class TestWhiteboardCreate:
    def test_valid_create(self):
        model = WhiteboardCreate(title="New Board")
        assert model.title == "New Board"
        assert model.board_data == {"version": 1, "elements": []}

    def test_custom_board_data(self):
        data = {"version": 2, "elements": [{"id": "1", "type": "rect"}]}
        model = WhiteboardCreate(title="Custom", board_data=data)
        assert model.board_data == data

    def test_empty_title_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            WhiteboardCreate(title="   ")


class TestWhiteboardRename:
    def test_valid_rename(self):
        model = WhiteboardRename(title="Renamed Board")
        assert model.title == "Renamed Board"

    def test_empty_rename_raises(self):
        with pytest.raises(ValidationError, match="cannot be blank"):
            WhiteboardRename(title="   ")

    def test_title_max_length(self):
        title = "a" * 255
        model = WhiteboardRename(title=title)
        assert len(model.title) == 255

    def test_title_exceeds_max_length(self):
        title = "a" * 256
        with pytest.raises(ValidationError):
            WhiteboardRename(title=title)


class TestWhiteboardAutosave:
    def test_valid_autosave(self):
        data = {"version": 1, "elements": [{"id": "1", "type": "rect"}]}
        model = WhiteboardAutosave(board_data=data)
        assert model.board_data == data

    def test_empty_board_data(self):
        model = WhiteboardAutosave(board_data={})
        assert model.board_data == {}


class TestWhiteboardResponse:
    def test_valid_response(self):
        board_id = UUID("12345678-1234-5678-1234-567812345678")
        user_id = UUID("87654321-4321-8765-4321-876543218765")
        now = datetime.now()
        data = {
            "id": board_id,
            "user_id": user_id,
            "title": "Board",
            "board_data": {"version": 1, "elements": []},
            "is_favorite": False,
            "is_archived": False,
            "is_deleted": False,
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
        }
        model = WhiteboardResponse(**data)
        assert model.id == board_id
        assert model.user_id == user_id
        assert model.title == "Board"

    def test_from_attributes_config(self):
        assert WhiteboardResponse.model_config.get("from_attributes") is True


class TestWhiteboardFilters:
    def test_valid_filters(self):
        model = WhiteboardFilters(
            is_archived=False,
            is_deleted=False,
            is_favorite=True,
            search="meeting",
        )
        assert model.is_archived is False
        assert model.is_deleted is False
        assert model.is_favorite is True
        assert model.search == "meeting"

    def test_defaults(self):
        model = WhiteboardFilters()
        assert model.is_archived is False
        assert model.is_deleted is False
        assert model.is_favorite is None
        assert model.search is None
