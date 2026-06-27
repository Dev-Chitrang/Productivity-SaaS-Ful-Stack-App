from uuid import UUID

class NoteDomainException(Exception):
    """Base domain exception for the notes module infrastructure."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class NoteNotFoundException(NoteDomainException):
    """Raised when a note does not exist or has been structurally filtered out."""
    def __init__(self, note_id: UUID):
        self.note_id = note_id
        super().__init__(f"Note with unique ID '{note_id}' was not found.")

class NoteAccessDeniedException(NoteDomainException):
    """Raised when a user attempts to interact with an entity owned by another user."""
    def __init__(self, note_id: UUID, user_id: UUID):
        self.note_id = note_id
        self.user_id = user_id
        super().__init__(f"User identity '{user_id}' does not have read/write access to note '{note_id}'.")

class NoteValidationError(NoteDomainException):
    """Raised when strict domain business rules are breached during processing."""
    pass
