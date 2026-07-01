from uuid import UUID

class WhiteboardDomainException(Exception):
    """Base exception for all domain-specific whiteboard operations."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class WhiteboardNotFoundException(WhiteboardDomainException):
    def __init__(self, board_id: UUID):
        self.board_id = board_id
        super().__init__(f"Whiteboard session with ID '{board_id}' was not found.")

class WhiteboardAccessDeniedException(WhiteboardDomainException):
    def __init__(self, board_id: UUID, user_id: UUID):
        self.board_id = board_id
        self.user_id = user_id
        super().__init__(f"User '{user_id}' does not have permission to access board '{board_id}'.")

class WhiteboardValidationError(WhiteboardDomainException):
    pass
