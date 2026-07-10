import uuid
import pytest
from app.modules.tasks.exceptions import (
    TaskDomainException,
    TaskNotFoundException,
    TaskAccessDeniedException,
    TaskValidationError,
)


class TestTaskDomainException:
    def test_is_exception(self):
        assert issubclass(TaskDomainException, Exception)

    def test_message_stored(self):
        exc = TaskDomainException("base error")
        assert exc.message == "base error"
        assert str(exc) == "base error"


class TestTaskNotFoundException:
    def test_is_task_domain_exception(self):
        assert issubclass(TaskNotFoundException, TaskDomainException)

    def test_message_contains_task_id(self):
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        exc = TaskNotFoundException(task_id)
        assert str(task_id) in str(exc)
        assert "was not found" in str(exc)

    def test_task_id_attribute(self):
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        exc = TaskNotFoundException(task_id)
        assert exc.task_id == task_id

    def test_can_be_raised(self):
        with pytest.raises(TaskNotFoundException):
            raise TaskNotFoundException(uuid.UUID("12345678-1234-5678-1234-567812345678"))

    def test_can_be_caught_as_task_domain_exception(self):
        with pytest.raises(TaskDomainException):
            raise TaskNotFoundException(uuid.UUID("12345678-1234-5678-1234-567812345678"))


class TestTaskAccessDeniedException:
    def test_is_task_domain_exception(self):
        assert issubclass(TaskAccessDeniedException, TaskDomainException)

    def test_message_contains_ids(self):
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        exc = TaskAccessDeniedException(task_id, user_id)
        assert str(task_id) in str(exc)
        assert str(user_id) in str(exc)
        assert "does not have permission" in str(exc)

    def test_task_id_attribute(self):
        task_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
        exc = TaskAccessDeniedException(task_id, user_id)
        assert exc.task_id == task_id
        assert exc.user_id == user_id

    def test_can_be_raised(self):
        with pytest.raises(TaskAccessDeniedException):
            raise TaskAccessDeniedException(
                uuid.UUID("12345678-1234-5678-1234-567812345678"),
                uuid.UUID("87654321-4321-8765-4321-876543218765"),
            )


class TestTaskValidationError:
    def test_is_task_domain_exception(self):
        assert issubclass(TaskValidationError, TaskDomainException)

    def test_message_stored(self):
        exc = TaskValidationError("validation failed")
        assert exc.message == "validation failed"
        assert str(exc) == "validation failed"

    def test_can_be_raised(self):
        with pytest.raises(TaskValidationError):
            raise TaskValidationError("bad input")

    def test_can_be_caught_as_task_domain_exception(self):
        with pytest.raises(TaskDomainException):
            raise TaskValidationError("bad input")
