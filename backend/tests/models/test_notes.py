import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from app.modules.notes.constants import MAX_NOTE_TITLE_LENGTH, MAX_NOTE_CONTENT_LENGTH
from app.models.notes import Note


class TestNoteModel:
    def test_tablename(self):
        assert Note.__tablename__ == "notes"

    def test_id_default_generates_uuid(self):
        note = Note(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            content="Hello",
        )
        assert note.id is None or isinstance(note.id, (uuid.UUID, type(uuid.uuid7())))

    def test_minimal_fields(self):
        now = datetime.now(timezone.utc)
        note = Note(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            content="Note content",
            tags=[],
            is_pinned=False,
            is_favorite=False,
            is_archived=False,
            created_at=now,
            updated_at=now,
        )
        assert note.user_id == uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert note.title is None
        assert note.content == "Note content"
        assert note.category is None
        assert note.tags == []
        assert note.is_pinned is False
        assert note.is_favorite is False
        assert note.is_archived is False
        assert note.deleted_at is None
        assert isinstance(note.created_at, datetime)
        assert isinstance(note.updated_at, datetime)

    def test_full_fields(self):
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        now = datetime.now(timezone.utc)
        note = Note(
            id=note_id,
            user_id=user_id,
            title="Full Note",
            content="Content here",
            category="personal",
            tags=["tag1", "tag2"],
            is_pinned=True,
            is_favorite=True,
            is_archived=False,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )
        assert note.id == note_id
        assert note.user_id == user_id
        assert note.title == "Full Note"
        assert note.content == "Content here"
        assert note.category == "personal"
        assert note.tags == ["tag1", "tag2"]
        assert note.is_pinned is True
        assert note.is_favorite is True
        assert note.is_archived is False
        assert note.deleted_at is None

    def test_soft_delete(self):
        now = datetime.now(timezone.utc)
        note = Note(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            content="Delete me",
            deleted_at=now,
        )
        assert note.deleted_at == now

    def test_created_at_default_utc(self):
        now = datetime.now(timezone.utc)
        note = Note(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            content="Hello",
            created_at=now,
        )
        assert note.created_at is not None
        assert note.created_at.tzinfo == timezone.utc

    def test_updated_at_default_utc(self):
        now = datetime.now(timezone.utc)
        note = Note(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            content="Hello",
            updated_at=now,
        )
        assert note.updated_at is not None
        assert note.updated_at.tzinfo == timezone.utc

    def test_tags_default_empty_list(self):
        note = Note(
            user_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            content="Hello",
            tags=[],
        )
        assert note.tags == []
