from typing import Optional, Sequence, List
from uuid import UUID
from datetime import datetime, timezone, date, timedelta, time
from sqlalchemy import select, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.reminders import UserReminderSetting
from app.models.meetings import Meeting
from app.models.calender import CalendarEvent
from app.models.tasks import Task
from app.modules.meetings.enums import MeetingType, MeetingStatus

MODULE_CONFIG_KEYS = {"calendar_config", "tasks_config", "meetings_config"}

class ReminderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: UUID) -> Optional[UserReminderSetting]:
        stmt = select(UserReminderSetting).where(UserReminderSetting.user_id == user_id)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def create_default_settings(self, user_id: UUID) -> UserReminderSetting:
        settings = UserReminderSetting(
            user_id=user_id,
            reminders_enabled=False,
            schedule_all=True,
            global_frequency="DAILY",
            global_time=datetime.strptime("09:00:00", "%H:%M:%S").time()
        )
        self.db.add(settings)
        await self.db.flush()
        return settings

    async def update_settings(self, settings: UserReminderSetting, data: dict) -> UserReminderSetting:
        for key, value in data.items():
            if value is not None:
                if key in MODULE_CONFIG_KEYS and isinstance(value, dict):
                    setattr(settings, key, self._serialize_module_config(value))
                elif key == "global_time" and isinstance(value, time):
                    setattr(settings, key, value)
                else:
                    setattr(settings, key, value)
        self.db.add(settings)
        await self.db.flush()
        return settings

    def _serialize_module_config(self, config: dict) -> dict:
        result = dict(config)
        if isinstance(result.get("time"), time):
            result["time"] = result["time"].strftime("%H:%M:%S")
        return result

    async def fetch_scheduled_meetings_for_reminders(self, current_time_marker: datetime) -> List[Meeting]:
        """
        Fetches only scheduled meetings starting within the next 24 hours.
        Strict indexation targets prevent full table sequential scanning workloads.
        """
        lower_bound = current_time_marker
        upper_bound = current_time_marker + timedelta(hours=24)

        stmt = select(Meeting).where(
            and_(
                Meeting.meeting_type == MeetingType.SCHEDULED,
                Meeting.status == MeetingStatus.SCHEDULED,
                Meeting.scheduled_start >= lower_bound,
                Meeting.scheduled_start <= upper_bound
            )
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def fetch_calendar_events_for_reminders(self, current_time_marker: datetime) -> List[CalendarEvent]:
        """Fetches upcoming calendar events starting within the next 24 hours."""
        lower_bound = current_time_marker
        upper_bound = current_time_marker + timedelta(hours=24)
        stmt = select(CalendarEvent).where(
            and_(
                CalendarEvent.start_time >= lower_bound,
                CalendarEvent.start_time <= upper_bound
            )
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def fetch_tasks_for_reminders(self, current_date_marker: date) -> List[Task]:
        """Fetches tasks that are due today, upcoming tomorrow, or overdue."""
        stmt = select(Task).where(
            and_(
                Task.is_completed == False,
                Task.due_date <= current_date_marker + timedelta(days=1)
            )
        )
        return list((await self.db.execute(stmt)).scalars().all())
