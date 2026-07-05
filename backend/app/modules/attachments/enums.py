from enum import Enum


class AttachmentEntityType(str, Enum):
    """
    Identifies which domain entity owns an attachment.
    Adding a new module requires only appending a value here.
    """
    TASK = "TASK"
    CALENDAR_EVENT = "CALENDAR_EVENT"
    MEETING_SESSION = "MEETING_SESSION"
    NOTE = "NOTE"


# Storage sub-directory for each entity type.
# Keeps filesystem layout predictable and independent of enum string values.
ENTITY_STORAGE_DIRS: dict[AttachmentEntityType, str] = {
    AttachmentEntityType.TASK: "tasks",
    AttachmentEntityType.CALENDAR_EVENT: "calendar_events",
    AttachmentEntityType.MEETING_SESSION: "meeting_sessions",
    AttachmentEntityType.NOTE: "notes",
}
