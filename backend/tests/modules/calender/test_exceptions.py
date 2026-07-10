import uuid
import pytest
from app.modules.calender.exceptions import (
    CalendarDomainException,
    EventNotFoundException,
    EventAccessDeniedException,
    CalendarValidationError,
)


class TestCalendarDomainException:
    def test_is_exception(self):
        assert issubclass(CalendarDomainException, Exception)

    def test_message_stored(self):
        exc = CalendarDomainException("base error")
        assert exc.message == "base error"
        assert str(exc) == "base error"


class TestEventNotFoundException:
    def test_is_calendar_domain_exception(self):
        assert issubclass(EventNotFoundException, CalendarDomainException)

    def test_message_contains_event_id(self):
        event_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        exc = EventNotFoundException(event_id)
        assert str(event_id) in str(exc)
        assert "was not found" in str(exc)

    def test_event_id_attribute(self):
        event_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        exc = EventNotFoundException(event_id)
        assert exc.event_id == event_id

    def test_can_be_raised(self):
        with pytest.raises(EventNotFoundException):
            raise EventNotFoundException(uuid.UUID("12345678-1234-5678-1234-567812345678"))

    def test_can_be_caught_as_calendar_domain_exception(self):
        with pytest.raises(CalendarDomainException):
            raise EventNotFoundException(uuid.UUID("12345678-1234-5678-1234-567812345678"))


class TestEventAccessDeniedException:
    def test_is_calendar_domain_exception(self):
        assert issubclass(EventAccessDeniedException, CalendarDomainException)

    def test_message_contains_ids(self):
        event_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        exc = EventAccessDeniedException(event_id, user_id)
        assert str(event_id) in str(exc)
        assert str(user_id) in str(exc)
        assert "does not have permission" in str(exc)

    def test_event_id_attribute(self):
        event_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        exc = EventAccessDeniedException(event_id, user_id)
        assert exc.event_id == event_id
        assert exc.user_id == user_id

    def test_can_be_raised(self):
        with pytest.raises(EventAccessDeniedException):
            raise EventAccessDeniedException(
                uuid.UUID("12345678-1234-5678-1234-567812345678"),
                uuid.UUID("87654321-4321-8765-4321-876543218765"),
            )


class TestCalendarValidationError:
    def test_is_calendar_domain_exception(self):
        assert issubclass(CalendarValidationError, CalendarDomainException)

    def test_message_stored(self):
        exc = CalendarValidationError("validation failed")
        assert exc.message == "validation failed"
        assert str(exc) == "validation failed"

    def test_can_be_raised(self):
        with pytest.raises(CalendarValidationError):
            raise CalendarValidationError("bad input")

    def test_can_be_caught_as_calendar_domain_exception(self):
        with pytest.raises(CalendarDomainException):
            raise CalendarValidationError("bad input")
