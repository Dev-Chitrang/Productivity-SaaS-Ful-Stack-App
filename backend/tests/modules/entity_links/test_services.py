from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.modules.entity_links.enums import EntityType
from app.modules.entity_links.exceptions import (
    EntityLinkNotFoundException,
    EntityLinkAccessDeniedException,
    EntityLinkValidationError,
)
from app.modules.entity_links.schemas import EntityLinkCreate
from app.modules.entity_links.services import EntityLinkService


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_repo):
    return EntityLinkService(mock_repo)


def _make_link(link_id=None, source_type="meeting", target_type="task", created_by=None):
    link = MagicMock()
    link.id = link_id or uuid4()
    link.source_type = source_type
    link.source_id = uuid4()
    link.target_type = target_type
    link.target_id = uuid4()
    link.created_by = created_by or uuid4()
    return link


class TestCreateLink:
    async def test_create_link_success(self, service, mock_repo):
        user_id = uuid4()
        payload = EntityLinkCreate(
            source_type=EntityType.MEETING,
            source_id=uuid4(),
            target_type=EntityType.TASK,
            target_id=uuid4(),
        )
        mock_link = _make_link(created_by=user_id)
        mock_repo.create.return_value = mock_link

        result = await service.create_link(user_id, payload)
        assert result == mock_link
        mock_repo.create.assert_called_once()
        call_data = mock_repo.create.call_args[0][0]
        assert call_data["created_by"] == user_id

    async def test_create_link_self_link_raises(self, service, mock_repo):
        link_id = uuid4()
        payload = EntityLinkCreate(
            source_type=EntityType.MEETING,
            source_id=link_id,
            target_type=EntityType.MEETING,
            target_id=link_id,
        )
        with pytest.raises(EntityLinkValidationError, match="Cannot link an entity to itself"):
            await service.create_link(uuid4(), payload)
        mock_repo.create.assert_not_called()


class TestGetLink:
    async def test_get_link_found_owner(self, service, mock_repo):
        user_id = uuid4()
        link = _make_link(created_by=user_id)
        mock_repo.get_by_id.return_value = link

        result = await service.get_link(user_id, link.id)
        assert result == link

    async def test_get_link_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(EntityLinkNotFoundException):
            await service.get_link(uuid4(), uuid4())

    async def test_get_link_access_denied(self, service, mock_repo):
        link = _make_link(created_by=uuid4())
        mock_repo.get_by_id.return_value = link
        with pytest.raises(EntityLinkAccessDeniedException):
            await service.get_link(uuid4(), link.id)


class TestDeleteLink:
    async def test_delete_link_success(self, service, mock_repo):
        user_id = uuid4()
        link = _make_link(created_by=user_id)
        mock_repo.get_by_id.return_value = link

        await service.delete_link(user_id, link.id)
        mock_repo.soft_delete.assert_called_once_with(link)

    async def test_delete_link_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(EntityLinkNotFoundException):
            await service.delete_link(uuid4(), uuid4())
        mock_repo.soft_delete.assert_not_called()


class TestListLinks:
    async def test_list_links_no_filters(self, service, mock_repo):
        user_id = uuid4()
        links = [_make_link(created_by=user_id), _make_link(created_by=uuid4())]
        mock_repo.list_links.return_value = links

        result = await service.list_links(user_id)
        assert len(result) == 1
        assert result[0].created_by == user_id
        mock_repo.list_links.assert_called_once()

    async def test_list_links_with_filters(self, service, mock_repo):
        user_id = uuid4()
        mock_repo.list_links.return_value = []

        source_id = uuid4()
        await service.list_links(user_id, source_type="meeting", source_id=source_id)
        mock_repo.list_links.assert_called_once_with(
            source_type="meeting", source_id=source_id, target_type=None, target_id=None
        )


class TestGetLinkedTasks:
    async def test_get_linked_tasks_empty(self, service, mock_repo):
        mock_repo.list_links.return_value = []
        result = await service.get_linked_tasks(uuid4(), uuid4())
        assert result == []
        mock_repo.db.execute.assert_not_called()

    async def test_get_linked_tasks_success(self, service, mock_repo):
        user_id = uuid4()
        link = _make_link(source_type="meeting", target_type="task", created_by=user_id)
        mock_repo.list_links.side_effect = [[link], []]
        task = MagicMock()
        task.id = link.target_id
        task.title = "Task 1"
        task.priority = MagicMock(value="HIGH")
        task.status = MagicMock(value="TODO")
        task.due_date = None
        task.user_id = user_id
        mock_exec = MagicMock()
        mock_exec.scalar_one_or_none.return_value = task
        mock_repo.db.execute.return_value = mock_exec

        result = await service.get_linked_tasks(user_id, uuid4())
        assert len(result) == 1
        assert result[0]["id"] == task.id
        assert result[0]["priority"] == "HIGH"
        assert result[0]["status"] == "TODO"
        assert result[0]["link_id"] == link.id

    async def test_get_linked_tasks_wrong_user_excluded(self, service, mock_repo):
        other_user = uuid4()
        user_id = uuid4()
        link = _make_link(source_type="meeting", target_type="task", created_by=user_id)
        mock_repo.list_links.side_effect = [[link], []]
        task = MagicMock()
        task.id = link.target_id
        task.priority = MagicMock(value="MEDIUM")
        task.status = MagicMock(value="TODO")
        task.due_date = None
        task.user_id = other_user
        mock_exec = MagicMock()
        mock_exec.scalar_one_or_none.return_value = task
        mock_repo.db.execute.return_value = mock_exec

        result = await service.get_linked_tasks(user_id, uuid4())
        assert result == []

    async def test_get_linked_tasks_priority_none_defaults_medium(self, service, mock_repo):
        user_id = uuid4()
        link = _make_link(target_type="task", created_by=user_id)
        mock_repo.list_links.side_effect = [[link], []]
        task = MagicMock()
        task.id = link.target_id
        task.priority = None
        task.status = MagicMock(value="TODO")
        task.due_date = None
        task.user_id = user_id
        mock_exec = MagicMock()
        mock_exec.scalar_one_or_none.return_value = task
        mock_repo.db.execute.return_value = mock_exec

        result = await service.get_linked_tasks(user_id, uuid4())
        assert result[0]["priority"] == "MEDIUM"

    async def test_get_linked_tasks_status_none_defaults_todo(self, service, mock_repo):
        user_id = uuid4()
        link = _make_link(target_type="task", created_by=user_id)
        mock_repo.list_links.side_effect = [[link], []]
        task = MagicMock()
        task.id = link.target_id
        task.priority = MagicMock(value="HIGH")
        task.status = None
        task.due_date = None
        task.user_id = user_id
        mock_exec = MagicMock()
        mock_exec.scalar_one_or_none.return_value = task
        mock_repo.db.execute.return_value = mock_exec

        result = await service.get_linked_tasks(user_id, uuid4())
        assert result[0]["status"] == "TODO"

    async def test_get_linked_tasks_reverse_link(self, service, mock_repo):
        user_id = uuid4()
        link = _make_link(source_type="task", target_type="meeting", created_by=user_id)
        mock_repo.list_links.side_effect = [[], [link]]
        task = MagicMock()
        task.id = link.source_id
        task.title = "Reverse Task"
        task.priority = MagicMock(value="LOW")
        task.status = MagicMock(value="IN_PROGRESS")
        task.due_date = datetime.now(timezone.utc)
        task.user_id = user_id
        mock_exec = MagicMock()
        mock_exec.scalar_one_or_none.return_value = task
        mock_repo.db.execute.return_value = mock_exec

        result = await service.get_linked_tasks(user_id, uuid4())
        assert len(result) == 1
        assert result[0]["id"] == link.source_id
        assert result[0]["link_id"] == link.id


class TestGetLinkedMeetings:
    async def test_get_linked_meetings_empty(self, service, mock_repo):
        mock_repo.list_links.return_value = []
        result = await service.get_linked_meetings(uuid4(), uuid4())
        assert result == []

    async def test_get_linked_meetings_own_task_and_host(self, service, mock_repo):
        user_id = uuid4()
        meeting_id = uuid4()
        link = _make_link(source_type="task", target_type="meeting", created_by=user_id)
        mock_repo.list_links.return_value = [link]
        meeting = MagicMock()
        meeting.id = link.target_id
        meeting.title = "Review Meeting"
        meeting.status = MagicMock(value="ACTIVE")
        meeting.meeting_code = "CODE-1"
        meeting.scheduled_start = datetime.now(timezone.utc)
        meeting.host_id = user_id
        mock_exec = MagicMock()
        mock_exec.scalars.return_value.all.return_value = [meeting]
        mock_repo.db.execute.return_value = mock_exec

        result = await service.get_linked_meetings(user_id, link.source_id)
        assert len(result) == 1
        assert result[0]["id"] == meeting.id
        assert result[0]["session_id"] is None

    async def test_get_linked_meetings_non_host_excluded(self, service, mock_repo):
        other_user = uuid4()
        link = _make_link(source_type="task", target_type="meeting", created_by=uuid4())
        mock_repo.list_links.return_value = [link]
        meeting = MagicMock()
        meeting.id = link.target_id
        meeting.status = MagicMock(value="ACTIVE")
        meeting.meeting_code = "CODE-2"
        meeting.scheduled_start = None
        meeting.host_id = other_user
        mock_exec = MagicMock()
        mock_exec.scalars.return_value.all.return_value = [meeting]
        mock_repo.db.execute.return_value = mock_exec

        result = await service.get_linked_meetings(uuid4(), link.source_id)
        assert result == []

    async def test_get_linked_meetings_via_session(self, service, mock_repo):
        user_id = uuid4()
        session_id = uuid4()
        meeting_id = uuid4()
        link = _make_link(source_type="task", target_type="meeting_session", created_by=user_id)
        # Ensure target_id matches the session ID used in the DB mock
        link.target_id = session_id
        mock_repo.list_links.return_value = [link]
        session = MagicMock()
        session.id = session_id
        session.meeting_id = meeting_id
        mock_session_exec = MagicMock()
        mock_session_exec.scalars.return_value.all.return_value = [session]
        meeting = MagicMock()
        meeting.id = meeting_id
        meeting.title = "Linked via Session"
        meeting.status = MagicMock(value="SCHEDULED")
        meeting.meeting_code = "CODE-3"
        meeting.scheduled_start = datetime.now(timezone.utc)
        meeting.host_id = user_id
        mock_meeting_exec = MagicMock()
        mock_meeting_exec.scalars.return_value.all.return_value = [meeting]
        mock_repo.db.execute.side_effect = [mock_session_exec, mock_meeting_exec]

        result = await service.get_linked_meetings(user_id, link.source_id)
        assert len(result) == 1
        assert result[0]["session_id"] == session_id
        assert result[0]["id"] == meeting_id

    async def test_get_linked_meetings_status_none_defaults_empty(self, service, mock_repo):
        user_id = uuid4()
        link = _make_link(source_type="task", target_type="meeting", created_by=user_id)
        mock_repo.list_links.return_value = [link]
        meeting = MagicMock()
        meeting.id = link.target_id
        meeting.status = None
        meeting.meeting_code = "CODE-4"
        meeting.scheduled_start = None
        meeting.host_id = user_id
        mock_exec = MagicMock()
        mock_exec.scalars.return_value.all.return_value = [meeting]
        mock_repo.db.execute.return_value = mock_exec

        result = await service.get_linked_meetings(user_id, link.source_id)
        assert result[0]["status"] == ""

    async def test_get_linked_meetings_all_directions(self, service, mock_repo):
        user_id = uuid4()
        link1 = _make_link(source_type="task", target_type="meeting", created_by=user_id)
        link2 = _make_link(source_type="meeting", target_type="task", created_by=uuid4())
        link3 = _make_link(source_type="task", target_type="meeting_session", created_by=user_id)
        link4 = _make_link(source_type="meeting_session", target_type="task", created_by=user_id)
        mock_repo.list_links.side_effect = [[link1], [link2], [link3], [link4]]
        meeting = MagicMock()
        meeting.id = link1.target_id
        meeting.title = "Multi-direction"
        meeting.status = MagicMock(value="ACTIVE")
        meeting.meeting_code = "CODE-5"
        meeting.scheduled_start = None
        meeting.host_id = user_id
        mock_exec = MagicMock()
        mock_exec.scalars.return_value.all.return_value = [meeting]
        mock_repo.db.execute.return_value = mock_exec

        result = await service.get_linked_meetings(user_id, link1.source_id)
        assert len(result) == 1


class TestGetLinkedTasksForSession:
    async def test_get_linked_tasks_for_session_empty(self, service, mock_repo):
        mock_repo.list_links.return_value = []
        result = await service.get_linked_tasks_for_session(uuid4(), uuid4())
        assert result == []

    async def test_get_linked_tasks_for_session_success(self, service, mock_repo):
        user_id = uuid4()
        link = _make_link(source_type="meeting_session", target_type="task", created_by=user_id)
        mock_repo.list_links.side_effect = [[link], []]
        task = MagicMock()
        task.id = link.target_id
        task.title = "Session Task"
        task.priority = MagicMock(value="MEDIUM")
        task.status = MagicMock(value="TODO")
        task.due_date = None
        task.user_id = user_id
        mock_exec = MagicMock()
        mock_exec.scalar_one_or_none.return_value = task
        mock_repo.db.execute.return_value = mock_exec

        result = await service.get_linked_tasks_for_session(user_id, uuid4())
        assert len(result) == 1
        assert result[0]["id"] == task.id
        assert result[0]["link_id"] == link.id

    async def test_get_linked_tasks_for_session_wrong_user_excluded(self, service, mock_repo):
        user_id = uuid4()
        other_user = uuid4()
        link = _make_link(source_type="meeting_session", target_type="task", created_by=other_user)
        mock_repo.list_links.side_effect = [[link], []]
        task = MagicMock()
        task.id = link.target_id
        task.priority = MagicMock(value="LOW")
        task.status = MagicMock(value="DONE")
        task.due_date = None
        task.user_id = user_id
        mock_exec = MagicMock()
        mock_exec.scalar_one_or_none.return_value = task
        mock_repo.db.execute.return_value = mock_exec

        result = await service.get_linked_tasks_for_session(user_id, uuid4())
        assert result == []

    async def test_get_linked_tasks_for_session_reverse_link(self, service, mock_repo):
        user_id = uuid4()
        link = _make_link(source_type="task", target_type="meeting_session", created_by=user_id)
        mock_repo.list_links.side_effect = [[], [link]]
        task = MagicMock()
        task.id = link.source_id
        task.title = "Reverse Session Task"
        task.priority = None
        task.status = MagicMock(value="IN_PROGRESS")
        task.due_date = datetime.now(timezone.utc)
        task.user_id = user_id
        mock_exec = MagicMock()
        mock_exec.scalar_one_or_none.return_value = task
        mock_repo.db.execute.return_value = mock_exec

        result = await service.get_linked_tasks_for_session(user_id, uuid4())
        assert len(result) == 1
        assert result[0]["priority"] == "MEDIUM"