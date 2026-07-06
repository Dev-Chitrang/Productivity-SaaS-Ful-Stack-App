from uuid import UUID


class AISuggestionDomainException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class AISuggestionNotFoundException(AISuggestionDomainException):
    def __init__(self, suggestion_id: UUID):
        self.suggestion_id = suggestion_id
        super().__init__(f"AI suggestion with ID '{suggestion_id}' was not found.")


class AISuggestionAccessDeniedException(AISuggestionDomainException):
    def __init__(self, suggestion_id: UUID, user_id: UUID):
        self.suggestion_id = suggestion_id
        self.user_id = user_id
        super().__init__(f"User '{user_id}' does not have permission to access suggestion '{suggestion_id}'.")


class AISuggestionValidationError(AISuggestionDomainException):
    pass
