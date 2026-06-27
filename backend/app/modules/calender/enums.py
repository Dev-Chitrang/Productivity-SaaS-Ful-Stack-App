from enum import Enum

class EventType(str, Enum):
    PERSONAL = "PERSONAL"
    MEETING = "MEETING"
    REMINDER = "REMINDER"

class EventColor(str, Enum):
    RED = "RED"
    BLUE = "BLUE"
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    PURPLE = "PURPLE"
    ORANGE = "ORANGE"
    GRAY = "GRAY"

class RecurrenceFrequency(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
