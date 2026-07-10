import pytest

from app.modules.entity_links.enums import RelationOrigin, EntityType


class TestRelationOrigin:
    def test_members(self):
        assert set(RelationOrigin) == {"USER", "SYSTEM", "AI"}

    def test_values(self):
        assert RelationOrigin.USER.value == "USER"
        assert RelationOrigin.SYSTEM.value == "SYSTEM"
        assert RelationOrigin.AI.value == "AI"

    def test_case_sensitive(self):
        assert RelationOrigin("USER") == RelationOrigin.USER
        with pytest.raises(ValueError):
            RelationOrigin("user")


class TestEntityType:
    def test_members(self):
        assert {e.value for e in EntityType} == {"meeting", "meeting_session", "task"}
        assert set(EntityType) == {EntityType.MEETING, EntityType.MEETING_SESSION, EntityType.TASK}

    def test_values_match_service_strings(self):
        assert EntityType.MEETING.value == "meeting"
        assert EntityType.MEETING_SESSION.value == "meeting_session"
        assert EntityType.TASK.value == "task"

    def test_from_string(self):
        assert EntityType("meeting") == EntityType.MEETING
        assert EntityType("task") == EntityType.TASK

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            EntityType("invalid")