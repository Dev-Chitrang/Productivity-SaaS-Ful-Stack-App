from uuid import UUID

class CalendarDomainException(Exception):
    """Base domain exception for the calendar module."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class EventNotFoundException(CalendarDomainException):
    """Raised when an event does not exist or has been soft-deleted."""
    def __init__(self, event_id: UUID):
        self.event_id = event_id
        super().__init__(f"Calendar event with ID '{event_id}' was not found.")

class EventAccessDeniedException(CalendarDomainException):
    """Raised when an authenticated user attempts to access an event belonging to another user."""
    def __init__(self, event_id: UUID, user_id: UUID):
        self.event_id = event_id
        self.user_id = user_id
        super().__init__(f"User '{user_id}' does not have permission to access event '{event_id}'.")

class CalendarValidationError(CalendarDomainException):
    """Raised when business logic rules are broken within the service layer."""
    pass
