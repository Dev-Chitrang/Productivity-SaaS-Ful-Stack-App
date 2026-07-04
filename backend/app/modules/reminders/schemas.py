import uuid
from pydantic import BaseModel, Field
from datetime import time
from typing import Optional, Dict, Any
from app.modules.reminders.enums import ReminderFrequency

class ModuleConfigSchema(BaseModel):
    enabled: bool = True
    frequency: ReminderFrequency = ReminderFrequency.DAILY
    time: time

class ReminderSettingUpdate(BaseModel):
    reminders_enabled: Optional[bool] = None
    schedule_all: bool
    global_frequency: Optional[ReminderFrequency] = None
    global_time: Optional[time] = None
    calendar_config: Optional[ModuleConfigSchema] = None
    tasks_config: Optional[ModuleConfigSchema] = None
    meetings_config: Optional[ModuleConfigSchema] = None

class ReminderSettingResponse(BaseModel):
    user_id: uuid.UUID
    reminders_enabled: bool
    schedule_all: bool
    global_frequency: Optional[ReminderFrequency]
    global_time: Optional[time]
    calendar_config: ModuleConfigSchema
    tasks_config: ModuleConfigSchema
    meetings_config: ModuleConfigSchema

    class Config:
        from_attributes = True
