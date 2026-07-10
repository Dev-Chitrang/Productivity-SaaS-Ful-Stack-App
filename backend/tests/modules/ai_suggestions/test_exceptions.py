import uuid

import pytest

from app.modules.ai_suggestions.exceptions import (
    AISuggestionDomainException,
    AISuggestionNotFoundException,
    AISuggestionAccessDeniedException,
    AISuggestionValidationError,
)


def _uuid(value: str) -> uuid.UUID:
    return uuid.UUID(value)


class TestAISuggestionDomainException:
    def test_base_stores_message(self):
        exc = AISuggestionDomainException("boom")
        assert exc.message == "boom"
        assert str(exc) == "boom"

    def test_base_is_exception(self):
        assert issubclass(AISuggestionDomainException, Exception)

    def test_subclasses_inherit_base(self):
        assert issubclass(AISuggestionNotFoundException, AISuggestionDomainException)
        assert issubclass(AISuggestionAccessDeniedException, AISuggestionDomainException)
        assert issubclass(AISuggestionValidationError, AISuggestionDomainException)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(AISuggestionDomainException):
            raise AISuggestionValidationError("invalid")


class TestAISuggestionNotFoundException:
    def test_stores_ids_and_message(self):
        sid = _uuid("12345678-1234-5678-1234-567812345678")
        exc = AISuggestionNotFoundException(sid)
        assert exc.suggestion_id == sid
        assert str(sid) in exc.message
        assert "was not found" in exc.message

    def test_is_raisable(self):
        sid = _uuid("12345678-1234-5678-1234-567812345678")
        with pytest.raises(AISuggestionNotFoundException):
            raise AISuggestionNotFoundException(sid)


class TestAISuggestionAccessDeniedException:
    def test_stores_ids_and_message(self):
        sid = _uuid("12345678-1234-5678-1234-567812345678")
        uid = _uuid("87654321-4321-8765-4321-876543218765")
        exc = AISuggestionAccessDeniedException(sid, uid)
        assert exc.suggestion_id == sid
        assert exc.user_id == uid
        assert str(sid) in exc.message
        assert str(uid) in exc.message
        assert "does not have permission" in exc.message

    def test_is_raisable(self):
        sid = _uuid("12345678-1234-5678-1234-567812345678")
        uid = _uuid("87654321-4321-8765-4321-876543218765")
        with pytest.raises(AISuggestionAccessDeniedException):
            raise AISuggestionAccessDeniedException(sid, uid)


class TestAISuggestionValidationError:
    def test_is_raisable_with_message(self):
        exc = AISuggestionValidationError("not pending")
        assert exc.message == "not pending"

    def test_is_caught_as_domain_exception(self):
        with pytest.raises(AISuggestionDomainException):
            raise AISuggestionValidationError("bad")
