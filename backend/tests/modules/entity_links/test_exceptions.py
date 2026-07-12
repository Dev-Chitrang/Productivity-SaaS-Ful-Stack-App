from uuid import uuid4
import pytest

from app.modules.entity_links.exceptions import (
    EntityLinkDomainException,
    EntityLinkNotFoundException,
    EntityLinkAccessDeniedException,
    EntityLinkValidationError,
)


class TestEntityLinkNotFoundException:
    def test_message_format(self):
        link_id = uuid4()
        exc = EntityLinkNotFoundException(link_id)
        assert exc.link_id == link_id
        assert str(exc) == f"EntityLink with ID '{link_id}' was not found."
        assert exc.message == f"EntityLink with ID '{link_id}' was not found."

    def test_is_domain_exception(self):
        exc = EntityLinkNotFoundException(uuid4())
        assert isinstance(exc, EntityLinkDomainException)
        assert isinstance(exc, Exception)


class TestEntityLinkAccessDeniedException:
    def test_message_format(self):
        link_id = uuid4()
        user_id = uuid4()
        exc = EntityLinkAccessDeniedException(link_id, user_id)
        assert exc.link_id == link_id
        assert exc.user_id == user_id
        assert str(exc) == f"User '{user_id}' does not have permission to access EntityLink '{link_id}'."
        assert exc.message == str(exc)

    def test_is_domain_exception(self):
        exc = EntityLinkAccessDeniedException(uuid4(), uuid4())
        assert isinstance(exc, EntityLinkDomainException)


class TestEntityLinkValidationError:
    def test_default_message(self):
        exc = EntityLinkValidationError("")
        assert str(exc) == ""
        assert exc.message == ""

    def test_custom_message(self):
        exc = EntityLinkValidationError("cannot link entity to itself")
        assert str(exc) == "cannot link entity to itself"
        assert exc.message == "cannot link entity to itself"

    def test_is_domain_exception(self):
        exc = EntityLinkValidationError("test")
        assert isinstance(exc, EntityLinkDomainException)