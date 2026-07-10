from datetime import datetime, timezone
from uuid import uuid4
import pytest
from pydantic import ValidationError

from app.modules.entity_links.enums import RelationOrigin, EntityType
from app.modules.entity_links.schemas import (
    EntityLinkCreate,
    EntityLinkResponse,
    EntityLinkListResponse,
    LinkedTaskResponse,
    LinkedMeetingResponse,
)


class TestEntityLinkCreate:
    def test_valid_minimal(self):
        payload = EntityLinkCreate(
            source_type=EntityType.MEETING,
            source_id=uuid4(),
            target_type=EntityType.TASK,
            target_id=uuid4(),
        )
        assert payload.source_type == EntityType.MEETING
        assert payload.target_type == EntityType.TASK
        assert payload.link_type == "RELATED_TO"
        assert payload.relation_origin == RelationOrigin.USER

    def test_invalid_source_type(self):
        with pytest.raises(ValidationError):
            EntityLinkCreate(
                source_type="invalid",
                source_id=uuid4(),
                target_type=EntityType.TASK,
                target_id=uuid4(),
            )

    def test_invalid_relation_origin(self):
        with pytest.raises(ValidationError):
            EntityLinkCreate(
                source_type=EntityType.MEETING,
                source_id=uuid4(),
                target_type=EntityType.TASK,
                target_id=uuid4(),
                relation_origin="INVALID",
            )

    def test_custom_link_type_and_origin(self):
        payload = EntityLinkCreate(
            source_type=EntityType.TASK,
            source_id=uuid4(),
            target_type=EntityType.MEETING,
            target_id=uuid4(),
            link_type="CUSTOM",
            relation_origin=RelationOrigin.AI,
        )
        assert payload.link_type == "CUSTOM"
        assert payload.relation_origin == RelationOrigin.AI


class TestEntityLinkResponse:
    def test_model_validate_from_orm(self):
        link_id = uuid4()
        now = datetime.now(timezone.utc)
        data = {
            "id": link_id,
            "source_type": "meeting",
            "source_id": uuid4(),
            "target_type": "task",
            "target_id": uuid4(),
            "link_type": "RELATED_TO",
            "relation_origin": RelationOrigin.USER,
            "created_by": uuid4(),
            "created_at": now,
            "deleted_at": None,
        }
        response = EntityLinkResponse.model_validate(data)
        assert response.id == link_id
        assert response.source_type == "meeting"
        assert response.deleted_at is None

    def test_deleted_at_present(self):
        now = datetime.now(timezone.utc)
        data = {
            "id": uuid4(),
            "source_type": "meeting",
            "source_id": uuid4(),
            "target_type": "task",
            "target_id": uuid4(),
            "link_type": "RELATED_TO",
            "relation_origin": RelationOrigin.USER,
            "created_by": uuid4(),
            "created_at": now,
            "deleted_at": now,
        }
        response = EntityLinkResponse.model_validate(data)
        assert response.deleted_at is not None


class TestEntityLinkListResponse:
    def test_empty_list(self):
        resp = EntityLinkListResponse(links=[], total_count=0)
        assert resp.total_count == 0
        assert resp.links == []

    def test_with_links(self):
        link = EntityLinkResponse(
            id=uuid4(),
            source_type="meeting",
            source_id=uuid4(),
            target_type="task",
            target_id=uuid4(),
            link_type="RELATED_TO",
            relation_origin=RelationOrigin.SYSTEM,
            created_by=uuid4(),
            created_at=datetime.now(timezone.utc),
        )
        resp = EntityLinkListResponse(links=[link], total_count=1)
        assert resp.total_count == 1
        assert len(resp.links) == 1
        assert resp.links[0].relation_origin == RelationOrigin.SYSTEM


class TestLinkedTaskResponse:
    def test_minimal_fields(self):
        task = LinkedTaskResponse(
            id=uuid4(),
            title="Task 1",
            priority="HIGH",
            status="TODO",
            link_id=uuid4(),
        )
        assert task.title == "Task 1"
        assert task.due_date is None
        assert task.link_id is not None

    def test_nullable_fields(self):
        task = LinkedTaskResponse(
            id=uuid4(),
            title="Task 2",
            priority="LOW",
            status="DONE",
            due_date=datetime.now(timezone.utc),
            link_id=None,
        )
        assert task.due_date is not None


class TestLinkedMeetingResponse:
    def test_with_session(self):
        session_id = uuid4()
        meeting = LinkedMeetingResponse(
            id=uuid4(),
            title="Sprint Review",
            status="ACTIVE",
            meeting_code="ABC-123",
            scheduled_start=datetime.now(timezone.utc),
            link_id=uuid4(),
            session_id=session_id,
        )
        assert meeting.session_id == session_id
        assert meeting.status == "ACTIVE"

    def test_nullable_fields(self):
        meeting = LinkedMeetingResponse(
            id=uuid4(),
            title="Standup",
            status="ENDED",
            meeting_code="XYZ-789",
            scheduled_start=None,
            link_id=None,
            session_id=None,
        )
        assert meeting.scheduled_start is None
        assert meeting.session_id is None