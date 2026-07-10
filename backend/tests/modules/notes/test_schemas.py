import uuid
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.modules.notes.constants import MAX_NOTE_TITLE_LENGTH, MAX_NOTE_CONTENT_LENGTH
from app.modules.notes.schemas import (
    NoteBase,
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    NoteListResponse,
)


class TestNoteBase:
    def test_valid_base(self):
        model = NoteBase(
            title="My Note",
            content="Content here",
            category="personal",
            tags=["tag1", "tag2"],
            is_pinned=True,
            is_favorite=False,
            is_archived=False,
        )
        assert model.title == "My Note"
        assert model.content == "Content here"
        assert model.category == "personal"
        assert sorted(model.tags) == ["tag1", "tag2"]
        assert model.is_pinned is True

    def test_title_strips_whitespace(self):
        model = NoteBase(title="  My Note  ", content="Content")
        assert model.title == "My Note"

    def test_tags_deduplicate_and_lower(self):
        model = NoteBase(
            title="Note",
            content="Content",
            tags=["Work", "work", "Personal"],
        )
        assert "work" in model.tags
        assert "personal" in model.tags
        assert len(model.tags) == 2

    def test_title_max_length(self):
        title = "a" * MAX_NOTE_TITLE_LENGTH
        model = NoteBase(title=title, content="Content")
        assert len(model.title) == MAX_NOTE_TITLE_LENGTH

    def test_title_exceeds_max_length(self):
        title = "a" * (MAX_NOTE_TITLE_LENGTH + 1)
        with pytest.raises(ValidationError):
            NoteBase(title=title, content="Content")

    def test_content_max_length(self):
        content = "a" * MAX_NOTE_CONTENT_LENGTH
        model = NoteBase(title="Note", content=content)
        assert len(model.content) == MAX_NOTE_CONTENT_LENGTH

    def test_content_exceeds_max_length(self):
        content = "a" * (MAX_NOTE_CONTENT_LENGTH + 1)
        with pytest.raises(ValidationError):
            NoteBase(title="Note", content=content)

    def test_category_max_length_100(self):
        model = NoteBase(title="Note", content="Content", category="a" * 100)
        assert len(model.category) == 100

    def test_category_exceeds_100_raises(self):
        with pytest.raises(ValidationError):
            NoteBase(title="Note", content="Content", category="a" * 101)

    def test_empty_title_allowed_with_content(self):
        model = NoteBase(title="", content="Content")
        assert model.title == ""

    def test_none_title_allowed(self):
        model = NoteBase(title=None, content="Content")
        assert model.title is None


class TestNoteCreate:
    def test_valid_create_with_title(self):
        model = NoteCreate(title="Note", content="Content")
        assert model.title == "Note"

    def test_valid_create_without_title(self):
        model = NoteCreate(content="Content only")
        assert model.title is None

    def test_empty_title_and_empty_content_raises(self):
        with pytest.raises(ValidationError, match="Empty notes are prohibited"):
            NoteCreate(title="   ", content="   ")

    def test_whitespace_only_title_and_content_raises(self):
        with pytest.raises(ValidationError):
            NoteCreate(title="\t\n", content="\t\n")

    def test_empty_title_with_content_ok(self):
        model = NoteCreate(title="", content="Content")
        assert model.content == "Content"

    def test_empty_content_with_title_ok(self):
        model = NoteCreate(title="Title", content="")
        assert model.title == "Title"

    def test_defaults(self):
        model = NoteCreate(title="Note", content="Content")
        assert model.is_pinned is False
        assert model.is_favorite is False
        assert model.is_archived is False
        assert model.tags == []


class TestNoteUpdate:
    def test_valid_partial_update(self):
        model = NoteUpdate(title="Updated Title", category="work")
        assert model.title == "Updated Title"
        assert model.category == "work"
        assert model.content is None

    def test_all_fields_optional(self):
        model = NoteUpdate()
        assert model.title is None
        assert model.content is None
        assert model.category is None
        assert model.tags is None

    def test_strip_to_empty_raises(self):
        with pytest.raises(ValidationError, match="Cannot strip notes down to an entirely empty state"):
            NoteUpdate(title="   ", content="   ")

    def test_title_only_strip_no_raise(self):
        NoteUpdate(title="   ", content=None)

    def test_title_only_ok(self):
        model = NoteUpdate(title="New Title")
        assert model.title == "New Title"

    def test_content_only_ok(self):
        model = NoteUpdate(content="New content")
        assert model.content == "New content"

    def test_tags_deduplicate_on_create(self):
        model = NoteBase(
            title="Note",
            content="Content",
            tags=["tag1", "tag1", "TAG2"],
        )
        assert len(model.tags) == 2
        assert "tag1" in model.tags
        assert "tag2" in model.tags

    def test_category_max_length_100(self):
        model = NoteUpdate(category="a" * 100)
        assert len(model.category) == 100

    def test_content_max_length(self):
        content = "a" * MAX_NOTE_CONTENT_LENGTH
        model = NoteUpdate(content=content)
        assert len(model.content) == MAX_NOTE_CONTENT_LENGTH


class TestNoteResponse:
    def test_valid_response(self):
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        now = datetime.now(timezone.utc)
        data = {
            "id": note_id,
            "user_id": user_id,
            "title": "My Note",
            "content": "Content",
            "category": "personal",
            "tags": ["tag1"],
            "is_pinned": True,
            "is_favorite": False,
            "is_archived": False,
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
        }
        model = NoteResponse(**data)
        assert model.id == note_id
        assert model.user_id == user_id
        assert model.title == "My Note"
        assert model.tags == ["tag1"]
        assert model.is_pinned is True

    def test_from_attributes_config(self):
        assert NoteResponse.model_config.get("from_attributes") is True


class TestNoteListResponse:
    def test_valid_list(self):
        now = datetime.now(timezone.utc)
        note = NoteResponse(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            user_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            title="Note",
            content="Content",
            created_at=now,
            updated_at=now,
        )
        model = NoteListResponse(notes=[note], total_count=1)
        assert len(model.notes) == 1
        assert model.total_count == 1

    def test_empty_list(self):
        model = NoteListResponse(notes=[], total_count=0)
        assert model.notes == []
        assert model.total_count == 0
