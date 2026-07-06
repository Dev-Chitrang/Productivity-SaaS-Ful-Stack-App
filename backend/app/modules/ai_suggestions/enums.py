from enum import Enum


class SuggestionStatus(str, Enum):
    PENDING = "PENDING"
    CREATED = "CREATED"
    REJECTED = "REJECTED"
