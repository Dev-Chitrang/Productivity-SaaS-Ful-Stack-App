from uuid import UUID

class TaskDomainException(Exception):
    """Base domain exception for the tasks module."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class TaskNotFoundException(TaskDomainException):
    """Raised when a task does not exist or has been soft-deleted."""
    def __init__(self, task_id: UUID):
        self.task_id = task_id
        super().__init__(f"Task with ID '{task_id}' was not found.")

class TaskAccessDeniedException(TaskDomainException):
    """Raised when a user tries to interact with a task they do not own."""
    def __init__(self, task_id: UUID, user_id: UUID):
        self.task_id = task_id
        self.user_id = user_id
        super().__init__(f"User '{user_id}' does not have permission to access task '{task_id}'.")

class TaskValidationError(TaskDomainException):
    """Raised when domain business rules or validation constraints fail."""
    pass
