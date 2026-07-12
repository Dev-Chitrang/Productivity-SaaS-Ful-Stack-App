import uuid
from datetime import datetime, timezone, timedelta, date, time
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.reminders.repository import ReminderRepository
from app.models.reminders import UserReminderSetting
from app.models.meetings import Meeting
from app.models.calender import CalendarEvent
from app.models.tasks import Task
from app.modules.meetings.enums import MeetingType, MeetingStatus


class TestReminderRepository:
    @pytest.fixture
    def db(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def repo(self, db):
        return ReminderRepository(db)

    async def test_get_by_user_id_found(self, repo, db):
        user_id = uuid.uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(spec=UserReminderSetting)
        db.execute.return_value = mock_result
        result = await repo.get_by_user_id(user_id)
        assert result is not None
        db.execute.assert_called_once()

    async def test_get_by_user_id_not_found(self, repo, db):
        user_id = uuid.uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result
        result = await repo.get_by_user_id(user_id)
        assert result is None

    async def test_create_default_settings(self, repo, db):
        user_id = uuid.uuid4()
        result = await repo.create_default_settings(user_id)
        assert isinstance(result, UserReminderSetting)
        assert result.user_id == user_id
        assert result.reminders_enabled is False
        assert result.global_frequency == "DAILY"
        db.add.assert_called_once()
        db.flush.assert_called_once()

    async def test_update_settings_all_fields(self, repo, db):
        settings = UserReminderSetting(
            user_id=uuid.uuid4(),
            reminders_enabled=False,
            schedule_all=True,
            global_frequency="DAILY",
            global_time=datetime.strptime("09:00:00", "%H:%M:%S").time()
        )
        data = {
            "reminders_enabled": True,
            "global_frequency": "WEEKLY",
            "global_time": time(10, 30, 0),
        }
        result = await repo.update_settings(settings, data)
        assert result.reminders_enabled is True
        assert result.global_frequency == "WEEKLY"
        assert result.global_time == time(10, 30, 0)
        db.add.assert_called_once_with(settings)
        db.flush.assert_called_once()

    async def test_update_settings_with_module_config(self, repo, db):
        settings = UserReminderSetting(
            user_id=uuid.uuid4(),
            reminders_enabled=True,
            schedule_all=False,
        )
        data = {
            "tasks_config": {
                "enabled": True,
                "frequency": "DAILY",
                "time": time(14, 0, 0),
            }
        }
        result = await repo.update_settings(settings, data)
        db.add.assert_called_once_with(settings)

    async def test_update_settings_none_values_skipped(self, repo, db):
        settings = UserReminderSetting(
            user_id=uuid.uuid4(),
            reminders_enabled=False,
        )
        data = {"reminders_enabled": None, "global_frequency": None}
        result = await repo.update_settings(settings, data)
        assert result.reminders_enabled is False
        assert result.global_frequency is None

    def test_serialize_module_config_with_time(self, repo):
        config = {"enabled": True, "frequency": "DAILY", "time": time(9, 0, 0)}
        result = repo._serialize_module_config(config)
        assert result["time"] == "09:00:00"

    def test_serialize_module_config_without_time(self, repo):
        config = {"enabled": True, "frequency": "DAILY"}
        result = repo._serialize_module_config(config)
        assert "time" not in result

    async def test_fetch_scheduled_meetings_for_reminders(self, repo, db):
        now = datetime.now(timezone.utc)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [MagicMock(spec=Meeting)]
        db.execute.return_value = mock_result
        result = await repo.fetch_scheduled_meetings_for_reminders(now)
        assert len(result) == 1

    async def test_fetch_scheduled_meetings_for_reminders_empty(self, repo, db):
        now = datetime.now(timezone.utc)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result
        result = await repo.fetch_scheduled_meetings_for_reminders(now)
        assert result == []

    async def test_fetch_calendar_events_for_reminders(self, repo, db):
        now = datetime.now(timezone.utc)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [MagicMock(spec=CalendarEvent)]
        db.execute.return_value = mock_result
        result = await repo.fetch_calendar_events_for_reminders(now)
        assert len(result) == 1

    async def test_fetch_tasks_for_reminders(self, repo, db):
        with patch("app.models.tasks.Task.is_completed", False, create=True):
            today = date.today()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [MagicMock(spec=Task)]
            db.execute.return_value = mock_result
            result = await repo.fetch_tasks_for_reminders(today)
            assert len(result) == 1
