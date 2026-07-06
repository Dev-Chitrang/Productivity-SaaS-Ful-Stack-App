from enum import Enum


class RelationOrigin(str, Enum):
    USER = "USER"
    SYSTEM = "SYSTEM"
    AI = "AI"


class EntityType(str, Enum):
    MEETING = "meeting"
    MEETING_SESSION = "meeting_session"
    TASK = "task"
