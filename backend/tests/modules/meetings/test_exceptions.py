import uuid

import pytest

from app.modules.meetings.exceptions import (
    MeetingDomainException,
    MeetingNotFoundException,
    MeetingAccessDeniedException,
    SessionAccessDeniedException,
    MeetingValidationError,
)


class BaseMeetingExceptionTests:
    def test_inherits_from_exception(self):
        assert issubclass(MeetingDomainException, Exception)

    def test_message_stored(self):
        exc = MeetingDomainException("something went wrong")
        assert exc.message == "something went wrong"
        assert str(exc) == "something went wrong"


class TestMeetingNotFoundException:
    def test_is_meeting_domain_exception(self):
        assert issubclass(MeetingNotFoundException, MeetingDomainException)

    def test_message_contains_meeting_id(self):
        mid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        exc = MeetingNotFoundException(mid)
        assert exc.meeting_id == mid
        assert str(mid) in str(exc)

    def test_default_message(self):
        mid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        exc = MeetingNotFoundException(mid)
        assert "Meeting entity" in str(exc)
        assert "was not found" in str(exc)


class TestMeetingAccessDeniedException:
    def test_is_meeting_domain_exception(self):
        assert issubclass(MeetingAccessDeniedException, MeetingDomainException)

    def test_message_contains_ids(self):
        mid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        uid = uuid.UUID("87654321-4321-8765-4321-876543218765")
        exc = MeetingAccessDeniedException(mid, uid)
        assert exc.meeting_id == mid
        assert exc.user_id == uid
        assert str(mid) in str(exc)
        assert str(uid) in str(exc)

    def test_default_message(self):
        mid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        uid = uuid.UUID("87654321-4321-8765-4321-876543218765")
        exc = MeetingAccessDeniedException(mid, uid)
        assert "does not have host privileges" in str(exc)


class TestSessionAccessDeniedException:
    def test_is_meeting_domain_exception(self):
        assert issubclass(SessionAccessDeniedException, MeetingDomainException)

    def test_message_contains_session_id(self):
        sid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        exc = SessionAccessDeniedException(sid)
        assert exc.session_id == sid
        assert str(sid) in str(exc)

    def test_message_contains_user_id_when_provided(self):
        sid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        uid = uuid.UUID("87654321-4321-8765-4321-876543218765")
        exc = SessionAccessDeniedException(sid, uid)
        assert exc.user_id == uid
        assert "Access denied" in str(exc)

    def test_user_id_defaults_none(self):
        sid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        exc = SessionAccessDeniedException(sid)
        assert exc.user_id is None


class TestMeetingValidationError:
    def test_is_meeting_domain_exception(self):
        assert issubclass(MeetingValidationError, MeetingDomainException)

    def test_custom_message(self):
        exc = MeetingValidationError("Invalid meeting state")
        assert str(exc) == "Invalid meeting state"

    def test_empty_message(self):
        exc = MeetingValidationError("")
        assert str(exc) == ""

    def test_can_be_raised_and_caught(self):
        with pytest.raises(MeetingValidationError):
            raise MeetingValidationError("boom")
