from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.modules.entity_links.dependencies import get_current_user_id, get_entity_link_service
from app.modules.entity_links.services import EntityLinkService


@pytest.fixture
def client():
    return TestClient(app)


def _override_auth(user_id=None):
    if user_id is None:
        user_id = uuid4()
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    return user_id


class TestCreateLinkRoute:
    def test_create_link_201(self, client):
        user_id = _override_auth()
        mock_service = AsyncMock(spec=EntityLinkService)
        mock_link = MagicMock()
        mock_link.id = uuid4()
        mock_link.source_type = "meeting"
        mock_link.source_id = uuid4()
        mock_link.target_type = "task"
        mock_link.target_id = uuid4()
        mock_link.link_type = "RELATED_TO"
        mock_link.relation_origin = "USER"
        mock_link.created_by = user_id
        mock_link.created_at.isoformat.return_value = "2024-01-01T00:00:00+00:00"
        mock_link.deleted_at = None
        mock_service.create_link.return_value = mock_link

        app.dependency_overrides[get_entity_link_service] = lambda: mock_service
        response = client.post(
            "/api/v1/entity-links",
            json={
                "source_type": "meeting",
                "source_id": str(uuid4()),
                "target_type": "task",
                "target_id": str(uuid4()),
            },
        )
        assert response.status_code == 201
        assert response.json()["id"] == str(mock_link.id)
        app.dependency_overrides.clear()


class TestDeleteLinkRoute:
    def test_delete_link_200(self, client):
        user_id = _override_auth()
        mock_service = AsyncMock(spec=EntityLinkService)
        mock_service.delete_link.return_value = {"status": "success", "message": "Link deleted successfully."}
        app.dependency_overrides[get_entity_link_service] = lambda: mock_service
        link_id = uuid4()
        response = client.delete(f"/api/v1/entity-links/{link_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        app.dependency_overrides.clear()

    def test_delete_link_404(self, client):
        user_id = _override_auth()
        mock_service = AsyncMock(spec=EntityLinkService)
        from fastapi import HTTPException
        mock_service.delete_link.side_effect = HTTPException(status_code=404, detail="Not found")
        app.dependency_overrides[get_entity_link_service] = lambda: mock_service
        response = client.delete(f"/api/v1/entity-links/{uuid4()}")
        assert response.status_code == 404
        app.dependency_overrides.clear()

    def test_delete_link_403(self, client):
        user_id = _override_auth()
        mock_service = AsyncMock(spec=EntityLinkService)
        from fastapi import HTTPException
        mock_service.delete_link.side_effect = HTTPException(status_code=403, detail="Forbidden")
        app.dependency_overrides[get_entity_link_service] = lambda: mock_service
        response = client.delete(f"/api/v1/entity-links/{uuid4()}")
        assert response.status_code == 403
        app.dependency_overrides.clear()


class TestListLinksRoute:
    def test_list_links_empty(self, client):
        user_id = _override_auth()
        mock_service = AsyncMock(spec=EntityLinkService)
        mock_service.list_links.return_value = []
        app.dependency_overrides[get_entity_link_service] = lambda: mock_service
        response = client.get("/api/v1/entity-links")
        assert response.status_code == 200
        json = response.json()
        assert json["total_count"] == 0
        assert json["links"] == []
        app.dependency_overrides.clear()

    def test_list_links_with_filters(self, client):
        user_id = _override_auth()
        mock_service = AsyncMock(spec=EntityLinkService)
        mock_service.list_links.return_value = []
        app.dependency_overrides[get_entity_link_service] = lambda: mock_service
        response = client.get(
            "/api/v1/entity-links",
            params={
                "source_type": "meeting",
                "source_id": str(uuid4()),
                "target_type": "task",
                "target_id": str(uuid4()),
            },
        )
        assert response.status_code == 200
        app.dependency_overrides.clear()


class TestLinkedTasksRoute:
    def test_get_linked_tasks_200(self, client):
        user_id = _override_auth()
        mock_service = AsyncMock(spec=EntityLinkService)
        mock_task = {
            "id": uuid4(),
            "title": "Task",
            "priority": "HIGH",
            "status": "TODO",
            "due_date": None,
            "link_id": uuid4(),
        }
        mock_service.get_linked_tasks.return_value = [mock_task]
        app.dependency_overrides[get_entity_link_service] = lambda: mock_service
        response = client.get(f"/api/v1/meetings/{uuid4()}/linked-tasks")
        assert response.status_code == 200
        json = response.json()
        assert len(json) == 1
        assert json[0]["title"] == "Task"
        app.dependency_overrides.clear()


class TestLinkedSessionTasksRoute:
    def test_get_linked_tasks_for_session_200(self, client):
        user_id = _override_auth()
        mock_service = AsyncMock(spec=EntityLinkService)
        mock_service.get_linked_tasks_for_session.return_value = []
        app.dependency_overrides[get_entity_link_service] = lambda: mock_service
        meeting_id = uuid4()
        session_id = uuid4()
        response = client.get(f"/api/v1/meetings/{meeting_id}/sessions/{session_id}/linked-tasks")
        assert response.status_code == 200
        app.dependency_overrides.clear()


class TestLinkedMeetingsRoute:
    def test_get_linked_meetings_200(self, client):
        user_id = _override_auth()
        mock_service = AsyncMock(spec=EntityLinkService)
        mock_service.get_linked_meetings.return_value = []
        app.dependency_overrides[get_entity_link_service] = lambda: mock_service
        response = client.get(f"/api/v1/tasks/{uuid4()}/linked-meetings")
        assert response.status_code == 200
        app.dependency_overrides.clear()