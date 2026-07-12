import uuid
import pytest
from app.modules.notes.exceptions import (
    NoteDomainException,
    NoteNotFoundException,
    NoteAccessDeniedException,
    NoteValidationError,
)


class TestNoteDomainException:
    def test_is_exception(self):
        assert issubclass(NoteDomainException, Exception)

    def test_message_stored(self):
        exc = NoteDomainException("base error")
        assert exc.message == "base error"
        assert str(exc) == "base error"


class TestNoteNotFoundException:
    def test_is_note_domain_exception(self):
        assert issubclass(NoteNotFoundException, NoteDomainException)

    def test_message_contains_note_id(self):
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        exc = NoteNotFoundException(note_id)
        assert str(note_id) in str(exc)
        assert "was not found" in str(exc)

    def test_note_id_attribute(self):
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        exc = NoteNotFoundException(note_id)
        assert exc.note_id == note_id

    def test_can_be_raised(self):
        with pytest.raises(NoteNotFoundException):
            raise NoteNotFoundException(uuid.UUID("12345678-1234-5678-1234-567812345678"))

    def test_can_be_caught_as_note_domain_exception(self):
        with pytest.raises(NoteDomainException):
            raise NoteNotFoundException(uuid.UUID("12345678-1234-5678-1234-567812345678"))


class TestNoteAccessDeniedException:
    def test_is_note_domain_exception(self):
        assert issubclass(NoteAccessDeniedException, NoteDomainException)

    def test_message_contains_ids(self):
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        exc = NoteAccessDeniedException(note_id, user_id)
        assert str(note_id) in str(exc)
        assert str(user_id) in str(exc)
        assert "does not have read/write access" in str(exc)

    def test_note_id_attribute(self):
        note_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        exc = NoteAccessDeniedException(note_id, user_id)
        assert exc.note_id == note_id
        assert exc.user_id == user_id

    def test_can_be_raised(self):
        with pytest.raises(NoteAccessDeniedException):
            raise NoteAccessDeniedException(
                uuid.UUID("12345678-1234-5678-1234-567812345678"),
                uuid.UUID("87654321-4321-8765-4321-876543218765"),
            )


class TestNoteValidationError:
    def test_is_note_domain_exception(self):
        assert issubclass(NoteValidationError, NoteDomainException)

    def test_message_stored(self):
        exc = NoteValidationError("validation failed")
        assert exc.message == "validation failed"
        assert str(exc) == "validation failed"

    def test_can_be_raised(self):
        with pytest.raises(NoteValidationError):
            raise NoteValidationError("bad input")

    def test_can_be_caught_as_note_domain_exception(self):
        with pytest.raises(NoteDomainException):
            raise NoteValidationError("bad input")
