from uuid import UUID


class EntityLinkDomainException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class EntityLinkNotFoundException(EntityLinkDomainException):
    def __init__(self, link_id: UUID):
        self.link_id = link_id
        super().__init__(f"EntityLink with ID '{link_id}' was not found.")


class EntityLinkAccessDeniedException(EntityLinkDomainException):
    def __init__(self, link_id: UUID, user_id: UUID):
        self.link_id = link_id
        self.user_id = user_id
        super().__init__(f"User '{user_id}' does not have permission to access EntityLink '{link_id}'.")


class EntityLinkValidationError(EntityLinkDomainException):
    pass
