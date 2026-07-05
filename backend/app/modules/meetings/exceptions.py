from uuid import UUID
from typing import Optional

class MeetingDomainException(Exception):
    """Base domain exception class for the meetings infrastructure module."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class MeetingNotFoundException(MeetingDomainException):
    """Raised when a meeting identifier does not match any valid record."""
    def __init__(self, meeting_id: UUID):
        self.meeting_id = meeting_id
        super().__init__(f"Meeting entity with unique ID '{meeting_id}' was not found.")

class MeetingAccessDeniedException(MeetingDomainException):
    """Raised when an unprivileged participant breaches host-only action boundaries."""
    def __init__(self, meeting_id: UUID, user_id: UUID):
        self.meeting_id = meeting_id
        self.user_id = user_id
        super().__init__(f"User ID '{user_id}' does not have host privileges for meeting '{meeting_id}'.")

class SessionAccessDeniedException(MeetingDomainException):
    """Raised when an unprivileged user attempts to access a session or its artifacts."""
    def __init__(self, session_id: UUID, user_id: Optional[UUID] = None):
        self.session_id = session_id
        self.user_id = user_id
        super().__init__(f"Access denied to session '{session_id}'.")

class MeetingValidationError(MeetingDomainException):
    """Raised when meeting-state lifecycle actions (e.g., starting an ended meeting) fail."""
    pass
