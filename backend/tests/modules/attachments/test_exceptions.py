import pytest
from uuid import UUID
from app.modules.attachments.exceptions import (
    AttachmentDomainException,
    AttachmentNotFoundException,
    AttachmentAccessDeniedException,
    AttachmentValidationError,
    AttachmentStorageError,
)


class TestAttachmentDomainException:
    def test_base_is_exception(self):
        assert issubclass(AttachmentDomainException, Exception)

    def test_base_message(self):
        exc = AttachmentDomainException("something went wrong")
        assert str(exc) == "something went wrong"

    def test_base_can_be_caught_as_exception(self):
        with pytest.raises(Exception):
            raise AttachmentDomainException("base error")


class TestAttachmentNotFoundException:
    def test_is_domain_exception(self):
        assert issubclass(AttachmentNotFoundException, AttachmentDomainException)

    def test_message_contains_id(self):
        attachment_id = UUID("12345678-1234-5678-1234-567812345678")
        exc = AttachmentNotFoundException(attachment_id)
        assert str(attachment_id) in str(exc)

    def test_message_format(self):
        attachment_id = UUID("12345678-1234-5678-1234-567812345678")
        exc = AttachmentNotFoundException(attachment_id)
        assert exc.message == f"Attachment '{attachment_id}' was not found."

    def test_stores_attachment_id(self):
        attachment_id = UUID("12345678-1234-5678-1234-567812345678")
        exc = AttachmentNotFoundException(attachment_id)
        assert exc.attachment_id == attachment_id


class TestAttachmentAccessDeniedException:
    def test_is_domain_exception(self):
        assert issubclass(AttachmentAccessDeniedException, AttachmentDomainException)

    def test_message_contains_user_and_attachment(self):
        attachment_id = UUID("12345678-1234-5678-1234-567812345678")
        user_id = UUID("87654321-4321-8765-4321-876543218765")
        exc = AttachmentAccessDeniedException(attachment_id, user_id)
        assert str(attachment_id) in str(exc)
        assert str(user_id) in str(exc)

    def test_message_without_user_id(self):
        attachment_id = UUID("12345678-1234-5678-1234-567812345678")
        exc = AttachmentAccessDeniedException(attachment_id)
        assert "None" in str(exc)

    def test_stores_attributes(self):
        attachment_id = UUID("12345678-1234-5678-1234-567812345678")
        user_id = UUID("87654321-4321-8765-4321-876543218765")
        exc = AttachmentAccessDeniedException(attachment_id, user_id)
        assert exc.attachment_id == attachment_id
        assert exc.user_id == user_id


class TestAttachmentValidationError:
    def test_is_domain_exception(self):
        assert issubclass(AttachmentValidationError, AttachmentDomainException)

    def test_message(self):
        exc = AttachmentValidationError("bad file")
        assert str(exc) == "bad file"

    def test_can_be_raised_and_caught(self):
        with pytest.raises(AttachmentValidationError):
            raise AttachmentValidationError("size too large")


class TestAttachmentStorageError:
    def test_is_domain_exception(self):
        assert issubclass(AttachmentStorageError, AttachmentDomainException)

    def test_message(self):
        exc = AttachmentStorageError("disk full")
        assert str(exc) == "disk full"

    def test_can_be_raised_and_caught(self):
        with pytest.raises(AttachmentStorageError):
            raise AttachmentStorageError("s3 unavailable")


class TestExceptionHierarchy:
    def test_not_found_is_not_access_denied(self):
        assert not issubclass(AttachmentNotFoundException, AttachmentAccessDeniedException)

    def test_validation_is_not_storage(self):
        assert not issubclass(AttachmentValidationError, AttachmentStorageError)

    def test_all_are_domain_exceptions(self):
        assert issubclass(AttachmentNotFoundException, AttachmentDomainException)
        assert issubclass(AttachmentAccessDeniedException, AttachmentDomainException)
        assert issubclass(AttachmentValidationError, AttachmentDomainException)
        assert issubclass(AttachmentStorageError, AttachmentDomainException)
