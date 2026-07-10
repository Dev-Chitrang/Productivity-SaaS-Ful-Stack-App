from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
import pytest

from app.modules.entity_links.controller import EntityLinkController
from app.modules.entity_links.services import EntityLinkService
from app.modules.entity_links.schemas import EntityLinkCreate
from app.modules.entity_links.exceptions import (
    EntityLinkNotFoundException,
    EntityLinkAccessDeniedException,
    EntityLinkValidationError,
)


@pytest.fixture
def mock_service():
    return AsyncMock(spec=EntityLinkService)


@pytest.fixture
def controller(mock_service):
    return EntityLinkController(mock_service)


class TestCreateLink:
    async def test_create_link_success(self, controller, mock_service):
        user_id = uuid4()
        payload = EntityLinkCreate(
            source_type="meeting",
            source_id=uuid4(),
            target_type="task",
            target_id=uuid4(),
        )
        mock_link = MagicMock()
        mock_service.create_link.return_value = mock_link
        with patch("app.modules.entity_links.controller.EntityLinkResponse.model_validate", return_value=mock_link):
            result = await controller.create_link(user_id, payload)
        mock_service.create_link.assert_called_once_with(user_id, payload)
        assert result == mock_link

    async def test_create_link_validation_error(self, controller, mock_service):
        mock_service.create_link.side_effect = EntityLinkValidationError("bad")
        payload = EntityLinkCreate(
            source_type="meeting",
            source_id=uuid4(),
            target_type="task",
            target_id=uuid4(),
        )
        with pytest.raises(HTTPException) as exc_info:
            await controller.create_link(uuid4(), payload)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert str(exc_info.value.detail) == "bad"


class TestDeleteLink:
    async def test_delete_link_success(self, controller, mock_service):
        result = await controller.delete_link(uuid4(), uuid4())
        assert result["status"] == "success"
        mock_service.delete_link.assert_called_once()

    async def test_delete_link_not_found(self, controller, mock_service):
        mock_service.delete_link.side_effect = EntityLinkNotFoundException(uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await controller.delete_link(uuid4(), uuid4())
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_link_access_denied(self, controller, mock_service):
        mock_service.delete_link.side_effect = EntityLinkAccessDeniedException(uuid4(), uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await controller.delete_link(uuid4(), uuid4())
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestListLinks:
    async def test_list_links_success(self, controller, mock_service):
        user_id = uuid4()
        mock_link = MagicMock()
        mock_service.list_links.return_value = [mock_link]
        with patch("app.modules.entity_links.controller.EntityLinkResponse.model_validate", return_value=mock_link), \
             patch("app.modules.entity_links.controller.EntityLinkListResponse") as MockListResponse:
            mock_instance = MagicMock()
            mock_instance.total_count = 1
            mock_instance.links = [mock_link]
            MockListResponse.return_value = mock_instance
            result = await controller.list_links(user_id)
        assert result.total_count == 1
        assert len(result.links) == 1

    async def test_list_links_with_filters(self, controller, mock_service):
        user_id = uuid4()
        source_id = uuid4()
        mock_service.list_links.return_value = []
        result = await controller.list_links(user_id, source_type="meeting", source_id=source_id)
        assert result.total_count == 0
        mock_service.list_links.assert_called_once_with(
            user_id, source_type="meeting", source_id=source_id, target_type=None, target_id=None
        )


class TestGetLinkedTasks:
    async def test_get_linked_tasks_success(self, controller, mock_service):
        mock_task = MagicMock()
        mock_service.get_linked_tasks.return_value = [mock_task]
        with patch("app.modules.entity_links.controller.LinkedTaskResponse.model_validate", return_value=mock_task):
            result = await controller.get_linked_tasks(uuid4(), uuid4())
        assert len(result) == 1


class TestGetLinkedMeetings:
    async def test_get_linked_meetings_success(self, controller, mock_service):
        mock_meeting = MagicMock()
        mock_service.get_linked_meetings.return_value = [mock_meeting]
        with patch("app.modules.entity_links.controller.LinkedMeetingResponse.model_validate", return_value=mock_meeting):
            result = await controller.get_linked_meetings(uuid4(), uuid4())
        assert len(result) == 1


class TestGetLinkedTasksForSession:
    async def test_get_linked_tasks_for_session_success(self, controller, mock_service):
        mock_task = MagicMock()
        mock_service.get_linked_tasks_for_session.return_value = [mock_task]
        with patch("app.modules.entity_links.controller.LinkedTaskResponse.model_validate", return_value=mock_task):
            result = await controller.get_linked_tasks_for_session(uuid4(), uuid4())
        assert len(result) == 1