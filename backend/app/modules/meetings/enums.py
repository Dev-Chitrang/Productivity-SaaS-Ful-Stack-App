from enum import Enum

class MeetingStatus(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    IDLE = "IDLE"
    ENDED = "ENDED"
    CANCELLED = "CANCELLED"

class ParticipantType(str, Enum):
    REGISTERED = "REGISTERED"
    GUEST = "GUEST"

class ParticipantStatus(str, Enum):
    WAITING = "WAITING"
    ADMITTED = "ADMITTED"
    LEFT = "LEFT"
    REMOVED = "REMOVED"
    REJECTED = "REJECTED"
