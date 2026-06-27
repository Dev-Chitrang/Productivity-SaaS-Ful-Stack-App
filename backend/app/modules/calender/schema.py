from datetime import datetime
from typing import Optional, List
from uuid import UUID
from zoneinfo import available_timezones
from pydantic import BaseModel, Field, field_validator, model_validator
from app.modules.calender.enums import EventType, EventColor, RecurrenceFrequency
from app.modules.calender.constants import MIN_RECURRENCE_INTERVAL, MAX_TITLE_LENGTH

_KNOWN_TIMEZONES = available_timezones()


def _validate_title_not_empty(value: str) -> str:
    if not value or not value.strip():
        raise ValueError("Event title cannot be empty or solely whitespace characters.")
    return value.strip()


def _validate_recurrence_interval(value: Optional[int]) -> Optional[int]:
    if value is not None and value < MIN_RECURRENCE_INTERVAL:
        raise ValueError(f"Recurrence interval must be >= {MIN_RECURRENCE_INTERVAL}.")
    return value


class CalendarEventBase(BaseModel):
    title: str = Field(..., max_length=MAX_TITLE_LENGTH, description="Title of the calendar event.")
    description: Optional[str] = Field(None, description="Detailed description context.")
    event_type: EventType = Field(default=EventType.PERSONAL)
    color: EventColor = Field(default=EventColor.BLUE)
    start_time: datetime = Field(..., description="Timezone-aware start datetime (UTC).")
    end_time: datetime = Field(..., description="Timezone-aware end datetime (UTC).")
    timezone: str = Field(default="UTC", description="Target local viewing timezone name string.")
    is_all_day: bool = Field(default=False)
    location: Optional[str] = Field(None, max_length=500)
    recurrence_frequency: Optional[RecurrenceFrequency] = None
    recurrence_interval: Optional[int] = None
    recurrence_end_date: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, value: str) -> str:
        return _validate_title_not_empty(value)

    @field_validator("recurrence_interval")
    @classmethod
    def validate_recurrence_interval(cls, value: Optional[int]) -> Optional[int]:
        return _validate_recurrence_interval(value)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        if value not in _KNOWN_TIMEZONES:
            raise ValueError(f"'{value}' is not a valid IANA timezone identifier.")
        return value


class CalendarEventCreate(CalendarEventBase):
    @model_validator(mode="after")
    def validate_datetime_ranges(self) -> "CalendarEventCreate":
        if self.start_time >= self.end_time:
            raise ValueError("Event start_time must be chronologically before end_time.")
        if self.recurrence_end_date and self.recurrence_end_date < self.start_time:
            raise ValueError("Recurrence end date cannot be chronologically before the event start_time.")
        return self


class CalendarEventUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=MAX_TITLE_LENGTH)
    description: Optional[str] = None
    event_type: Optional[EventType] = None
    color: Optional[EventColor] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timezone: Optional[str] = None
    is_all_day: Optional[bool] = None
    location: Optional[str] = Field(None, max_length=500)
    recurrence_frequency: Optional[RecurrenceFrequency] = None
    recurrence_interval: Optional[int] = None
    recurrence_end_date: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return _validate_title_not_empty(value)

    @field_validator("recurrence_interval")
    @classmethod
    def validate_recurrence_interval(cls, value: Optional[int]) -> Optional[int]:
        return _validate_recurrence_interval(value)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if value not in _KNOWN_TIMEZONES:
            raise ValueError(f"'{value}' is not a valid IANA timezone identifier.")
        return value

    @model_validator(mode="after")
    def validate_datetime_ranges(self) -> "CalendarEventUpdate":
        if self.start_time is not None and self.end_time is not None:
            if self.start_time >= self.end_time:
                raise ValueError("Event start_time must be chronologically before end_time.")
        return self

class CalendarEventResponse(CalendarEventBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CalendarOccurrenceResponse(BaseModel):
    """
    A single event occurrence returned to the client.

    For non-recurring events this maps 1:1 to the stored record.
    For recurring events this represents one expanded occurrence within
    the requested date range — the frontend renders it as-is.
    """
    id: UUID = Field(..., description="Original event ID (series anchor for recurring events).")
    title: str
    description: Optional[str]
    event_type: EventType
    color: EventColor
    start_time: datetime
    end_time: datetime
    timezone: str
    is_all_day: bool
    location: Optional[str]
    is_recurring: bool = Field(default=False)
    recurrence_frequency: Optional[RecurrenceFrequency] = None
    recurrence_interval: Optional[int] = None
    recurrence_end_date: Optional[datetime] = None

    class Config:
        from_attributes = True
