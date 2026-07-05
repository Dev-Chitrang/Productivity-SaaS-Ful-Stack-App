from enum import Enum

class MeetingType(str, Enum):
    INSTANT = "INSTANT"
    SCHEDULED = "SCHEDULED"

class MeetingStatus(str, Enum):
    CREATED = "CREATED"
    SCHEDULED = "SCHEDULED"
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

class AIAnalysisStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
