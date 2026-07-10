import uuid
import pytest
from app.modules.whiteboard.exceptions import (
    WhiteboardDomainException,
    WhiteboardNotFoundException,
    WhiteboardAccessDeniedException,
    WhiteboardValidationError,
)


class TestWhiteboardDomainException:
    def test_is_exception(self):
        assert issubclass(WhiteboardDomainException, Exception)

    def test_message_stored(self):
        exc = WhiteboardDomainException("base error")
        assert exc.message == "base error"
        assert str(exc) == "base error"


class TestWhiteboardNotFoundException:
    def test_is_whiteboard_domain_exception(self):
        assert issubclass(WhiteboardNotFoundException, WhiteboardDomainException)

    def test_message_contains_board_id(self):
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        exc = WhiteboardNotFoundException(board_id)
        assert str(board_id) in str(exc)
        assert "was not found" in str(exc)

    def test_board_id_attribute(self):
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        exc = WhiteboardNotFoundException(board_id)
        assert exc.board_id == board_id

    def test_can_be_raised(self):
        with pytest.raises(WhiteboardNotFoundException):
            raise WhiteboardNotFoundException(uuid.UUID("12345678-1234-5678-1234-567812345678"))

    def test_can_be_caught_as_whiteboard_domain_exception(self):
        with pytest.raises(WhiteboardDomainException):
            raise WhiteboardNotFoundException(uuid.UUID("12345678-1234-5678-1234-567812345678"))


class TestWhiteboardAccessDeniedException:
    def test_is_whiteboard_domain_exception(self):
        assert issubclass(WhiteboardAccessDeniedException, WhiteboardDomainException)

    def test_message_contains_ids(self):
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        exc = WhiteboardAccessDeniedException(board_id, user_id)
        assert str(board_id) in str(exc)
        assert str(user_id) in str(exc)
        assert "does not have permission" in str(exc)

    def test_board_id_attribute(self):
        board_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        exc = WhiteboardAccessDeniedException(board_id, user_id)
        assert exc.board_id == board_id
        assert exc.user_id == user_id

    def test_can_be_raised(self):
        with pytest.raises(WhiteboardAccessDeniedException):
            raise WhiteboardAccessDeniedException(
                uuid.UUID("12345678-1234-5678-1234-567812345678"),
                uuid.UUID("87654321-4321-8765-4321-876543218765"),
            )


class TestWhiteboardValidationError:
    def test_is_whiteboard_domain_exception(self):
        assert issubclass(WhiteboardValidationError, WhiteboardDomainException)

    def test_message_stored(self):
        exc = WhiteboardValidationError("validation failed")
        assert exc.message == "validation failed"
        assert str(exc) == "validation failed"

    def test_can_be_raised(self):
        with pytest.raises(WhiteboardValidationError):
            raise WhiteboardValidationError("bad input")

    def test_can_be_caught_as_whiteboard_domain_exception(self):
        with pytest.raises(WhiteboardDomainException):
            raise WhiteboardValidationError("bad input")
