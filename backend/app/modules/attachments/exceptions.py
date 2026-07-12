from uuid import UUID
from typing import Optional


class AttachmentDomainException(Exception):
    """Base domain exception for the attachments infrastructure module."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class AttachmentNotFoundException(AttachmentDomainException):
    """Raised when an attachment record cannot be located by its identifier."""
    def __init__(self, attachment_id: UUID):
        self.attachment_id = attachment_id
        super().__init__(f"Attachment '{attachment_id}' was not found.")


class AttachmentAccessDeniedException(AttachmentDomainException):
    """Raised when the requesting user does not own the attachment."""
    def __init__(self, attachment_id: UUID, user_id: Optional[UUID] = None):
        self.attachment_id = attachment_id
        self.user_id = user_id
        super().__init__(
            f"User '{user_id}' does not have access to attachment '{attachment_id}'."
        )


class AttachmentValidationError(AttachmentDomainException):
    """Raised when upload input fails validation rules (type, size, filename)."""
    pass


class AttachmentStorageError(AttachmentDomainException):
    """Raised when a filesystem or storage provider operation fails."""
    pass
