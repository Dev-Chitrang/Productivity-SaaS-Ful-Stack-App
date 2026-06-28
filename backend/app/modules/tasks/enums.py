from enum import Enum

class TaskStatus(str, Enum):
    TODO = 'TODO'
    IN_PROGRESS = 'IN PROGRESS'
    DONE = 'DONE'

class TaskPriority(str, Enum):
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
