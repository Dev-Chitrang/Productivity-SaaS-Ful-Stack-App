import pytest
from app.modules.attachments.enums import AttachmentEntityType, ENTITY_STORAGE_DIRS


class TestAttachmentEntityType:
    def test_task_value(self):
        assert AttachmentEntityType.TASK == "TASK"

    def test_calendar_event_value(self):
        assert AttachmentEntityType.CALENDAR_EVENT == "CALENDAR_EVENT"

    def test_meeting_session_value(self):
        assert AttachmentEntityType.MEETING_SESSION == "MEETING_SESSION"

    def test_note_value(self):
        assert AttachmentEntityType.NOTE == "NOTE"

    def test_is_string_enum(self):
        assert issubclass(AttachmentEntityType, str)

    def test_has_four_members(self):
        assert len(list(AttachmentEntityType)) == 4

    def test_values_are_strings(self):
        for member in AttachmentEntityType:
            assert isinstance(member.value, str)


class TestEntityStorageDirs:
    def test_task_maps_to_tasks_dir(self):
        assert ENTITY_STORAGE_DIRS[AttachmentEntityType.TASK] == "tasks"

    def test_calendar_event_maps_to_calendar_dir(self):
        assert ENTITY_STORAGE_DIRS[AttachmentEntityType.CALENDAR_EVENT] == "calendar_events"

    def test_meeting_session_maps_to_meetings_dir(self):
        assert ENTITY_STORAGE_DIRS[AttachmentEntityType.MEETING_SESSION] == "meeting_sessions"

    def test_note_maps_to_notes_dir(self):
        assert ENTITY_STORAGE_DIRS[AttachmentEntityType.NOTE] == "notes"

    def test_all_entity_types_covered(self):
        assert set(ENTITY_STORAGE_DIRS.keys()) == set(AttachmentEntityType)

    def test_no_none_values(self):
        for v in ENTITY_STORAGE_DIRS.values():
            assert v is not None
            assert isinstance(v, str)
            assert len(v) > 0
