import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.modules.reminders.notification_service import (
    snapshot_settings,
    _compute_changes,
    _format_time,
    _format_frequency,
    _format_timestamp,
    _get_effective_module_state,
    _module_display_line,
    _build_module_info,
    send_reminder_confirmation,
    _send_created_email,
    _send_updated_email,
)
from app.models.reminders import UserReminderSetting


class TestHelpers:
    def test_format_time_none(self):
        assert _format_time(None) == ""

    def test_format_time_empty(self):
        assert _format_time("") == ""

    def test_format_time_valid_am(self):
        result = _format_time("09:30:00")
        assert "09:30 AM" in result

    def test_format_time_valid_pm(self):
        result = _format_time("14:30:00")
        assert "02:30 PM" in result

    def test_format_time_midnight(self):
        result = _format_time("00:00:00")
        assert "12:00 AM" in result

    def test_format_time_noon(self):
        result = _format_time("12:00:00")
        assert "12:00 PM" in result

    def test_format_time_invalid(self):
        result = _format_time("not-a-time")
        assert result == "not-a-time"

    def test_format_frequency_none(self):
        assert _format_frequency(None) == ""

    def test_format_frequency_empty(self):
        assert _format_frequency("") == ""

    def test_format_frequency_valid(self):
        assert _format_frequency("DAILY") == "Daily"

    def test_format_timestamp_default(self):
        result = _format_timestamp()
        assert "UTC" in result

    def test_format_timestamp_with_dt(self):
        dt = datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc)
        result = _format_timestamp(dt, "UTC")
        assert "15 Jan 2024" in result
        assert "10:30 AM" in result

    def test_format_timestamp_with_tz(self):
        dt = datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc)
        result = _format_timestamp(dt, "EST")
        assert "EST" in result

    def test_module_display_line_full(self):
        config = {"frequency": "DAILY", "time": "09:00:00"}
        result = _module_display_line(config, "UTC")
        assert "Frequency: Daily" in result
        assert "09:00 AM" in result
        assert "UTC" in result

    def test_module_display_line_empty(self):
        result = _module_display_line({})
        assert result == "\u2014"

    def test_module_display_line_freq_only(self):
        config = {"frequency": "WEEKLY"}
        result = _module_display_line(config)
        assert "Frequency: Weekly" in result

    def test_build_module_info_full(self):
        config = {"frequency": "DAILY", "time": "09:00:00"}
        result = _build_module_info(config, "UTC")
        assert result["frequency"] == "Daily"
        assert result["time"] == "09:00 AM"
        assert result["timezone"] == "UTC"

    def test_get_effective_module_state_disabled(self):
        snapshot = {"reminders_enabled": False}
        result = _get_effective_module_state("tasks_config", snapshot)
        assert result["enabled"] is False

    def test_get_effective_module_state_schedule_all(self):
        snapshot = {
            "reminders_enabled": True,
            "schedule_all": True,
            "global_frequency": "DAILY",
            "global_time": "09:00:00",
        }
        result = _get_effective_module_state("tasks_config", snapshot)
        assert result["enabled"] is True
        assert result["frequency"] == "DAILY"
        assert result["time"] == "09:00:00"

    def test_get_effective_module_state_per_module_enabled(self):
        snapshot = {
            "reminders_enabled": True,
            "schedule_all": False,
            "tasks_config": {"enabled": True, "frequency": "WEEKLY", "time": "10:00:00"},
        }
        result = _get_effective_module_state("tasks_config", snapshot)
        assert result["enabled"] is True
        assert result["frequency"] == "WEEKLY"

    def test_get_effective_module_state_per_module_disabled(self):
        snapshot = {
            "reminders_enabled": True,
            "schedule_all": False,
            "tasks_config": {"enabled": False},
        }
        result = _get_effective_module_state("tasks_config", snapshot)
        assert result["enabled"] is False
        assert result["frequency"] is None

    def test_get_effective_module_state_missing_config(self):
        snapshot = {
            "reminders_enabled": True,
            "schedule_all": False,
            "tasks_config": None,
        }
        result = _get_effective_module_state("tasks_config", snapshot)
        assert result["enabled"] is False


class TestSnapshotSettings:
    def test_snapshot_full(self):
        settings = MagicMock(spec=UserReminderSetting)
        settings.reminders_enabled = True
        settings.schedule_all = True
        settings.global_frequency = "DAILY"
        settings.global_time = datetime.strptime("09:00:00", "%H:%M:%S").time()
        settings.tasks_config = {}
        settings.meetings_config = {}
        settings.calendar_config = {}

        result = snapshot_settings(settings)
        assert result["reminders_enabled"] is True
        assert result["schedule_all"] is True
        assert result["global_frequency"] == "DAILY"
        assert result["global_time"] == "09:00:00"

    def test_snapshot_global_time_none(self):
        settings = MagicMock(spec=UserReminderSetting)
        settings.reminders_enabled = False
        settings.schedule_all = True
        settings.global_frequency = None
        settings.global_time = None
        settings.tasks_config = None
        settings.meetings_config = None
        settings.calendar_config = None

        result = snapshot_settings(settings)
        assert result["global_time"] is None

    def test_snapshot_with_module_config(self):
        settings = MagicMock(spec=UserReminderSetting)
        settings.reminders_enabled = True
        settings.schedule_all = False
        settings.global_frequency = None
        settings.global_time = None
        settings.tasks_config = {"enabled": True, "frequency": "DAILY", "time": "09:00:00"}
        settings.meetings_config = None
        settings.calendar_config = None

        result = snapshot_settings(settings)
        assert result["tasks_config"]["enabled"] is True
        assert result["meetings_config"]["enabled"] is False


class TestComputeChanges:
    def test_no_changes(self):
        old = {
            "reminders_enabled": True, "schedule_all": True,
            "global_frequency": "DAILY", "global_time": "09:00:00",
            "tasks_config": {"enabled": True, "frequency": "DAILY", "time": "09:00:00"},
            "meetings_config": {"enabled": False, "frequency": None, "time": None},
            "calendar_config": {"enabled": False, "frequency": None, "time": None},
        }
        new = dict(old)
        modified, disabled, enabled = _compute_changes(old, new)
        assert len(modified) == 0
        assert len(disabled) == 0
        assert len(enabled) == 0

    def test_module_disabled(self):
        old = {
            "reminders_enabled": True, "schedule_all": True,
            "global_frequency": "DAILY", "global_time": "09:00:00",
            "tasks_config": {"enabled": True, "frequency": "DAILY", "time": "09:00:00"},
            "meetings_config": {"enabled": False, "frequency": None, "time": None},
            "calendar_config": {"enabled": False, "frequency": None, "time": None},
        }
        new = {
            "reminders_enabled": True, "schedule_all": False,
            "global_frequency": "DAILY", "global_time": "09:00:00",
            "tasks_config": {"enabled": False, "frequency": None, "time": None},
            "meetings_config": {"enabled": False, "frequency": None, "time": None},
            "calendar_config": {"enabled": False, "frequency": None, "time": None},
        }
        modified, disabled, enabled = _compute_changes(old, new)
        assert "Tasks" in disabled
        assert len(enabled) == 0

    def test_module_enabled(self):
        old = {
            "reminders_enabled": True, "schedule_all": False,
            "global_frequency": None, "global_time": None,
            "tasks_config": {"enabled": False, "frequency": None, "time": None},
            "meetings_config": {"enabled": False, "frequency": None, "time": None},
            "calendar_config": {"enabled": False, "frequency": None, "time": None},
        }
        new = {
            "reminders_enabled": True, "schedule_all": False,
            "global_frequency": None, "global_time": None,
            "tasks_config": {"enabled": True, "frequency": "DAILY", "time": "09:00:00"},
            "meetings_config": {"enabled": False, "frequency": None, "time": None},
            "calendar_config": {"enabled": False, "frequency": None, "time": None},
        }
        modified, disabled, enabled = _compute_changes(old, new)
        assert len(enabled) == 1
        assert enabled[0]["name"] == "Tasks"

    def test_module_modified(self):
        old = {
            "reminders_enabled": True, "schedule_all": False,
            "global_frequency": None, "global_time": None,
            "tasks_config": {"enabled": True, "frequency": "DAILY", "time": "09:00:00"},
            "meetings_config": {"enabled": False, "frequency": None, "time": None},
            "calendar_config": {"enabled": False, "frequency": None, "time": None},
        }
        new = {
            "reminders_enabled": True, "schedule_all": False,
            "global_frequency": None, "global_time": None,
            "tasks_config": {"enabled": True, "frequency": "WEEKLY", "time": "10:00:00"},
            "meetings_config": {"enabled": False, "frequency": None, "time": None},
            "calendar_config": {"enabled": False, "frequency": None, "time": None},
        }
        modified, disabled, enabled = _compute_changes(old, new)
        assert len(modified) == 1
        assert modified[0]["name"] == "Tasks"


class TestSendReminderConfirmation:
    async def test_user_not_found(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await send_reminder_confirmation(
            db, uuid.uuid4(), True, {}, {}
        )
        assert result is None

    async def test_user_no_email(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(email=None)
        db.execute.return_value = mock_result

        result = await send_reminder_confirmation(
            db, uuid.uuid4(), True, {}, {}
        )
        assert result is None

    async def test_send_created_email(self):
        db = AsyncMock()
        user = MagicMock(
            email="test@example.com",
            full_name="Test User",
            timezone="UTC",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        db.execute.return_value = mock_result

        new_snapshot = {
            "reminders_enabled": True,
            "schedule_all": True,
            "global_frequency": "DAILY",
            "global_time": "09:00:00",
            "tasks_config": {"enabled": True, "frequency": "DAILY", "time": "09:00:00"},
            "meetings_config": {"enabled": False, "frequency": None, "time": None},
            "calendar_config": {"enabled": False, "frequency": None, "time": None},
        }

        with patch("app.modules.reminders.notification_service._send_created_email", new_callable=AsyncMock) as mock_send:
            await send_reminder_confirmation(
                db, uuid.uuid4(), is_new=True, old_snapshot={}, new_snapshot=new_snapshot
            )
            mock_send.assert_called_once()

    async def test_send_updated_email(self):
        db = AsyncMock()
        user = MagicMock(
            email="test@example.com",
            full_name="Test User",
            timezone="UTC",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        db.execute.return_value = mock_result

        old = {
            "reminders_enabled": True, "schedule_all": True,
            "global_frequency": "DAILY", "global_time": "09:00:00",
            "tasks_config": {"enabled": True, "frequency": "DAILY", "time": "09:00:00"},
            "meetings_config": {"enabled": False, "frequency": None, "time": None},
            "calendar_config": {"enabled": False, "frequency": None, "time": None},
        }
        new = {
            "reminders_enabled": True, "schedule_all": False,
            "global_frequency": "DAILY", "global_time": "09:00:00",
            "tasks_config": {"enabled": False, "frequency": None, "time": None},
            "meetings_config": {"enabled": False, "frequency": None, "time": None},
            "calendar_config": {"enabled": False, "frequency": None, "time": None},
        }

        with patch("app.modules.reminders.notification_service._send_updated_email", new_callable=AsyncMock) as mock_send:
            await send_reminder_confirmation(
                db, uuid.uuid4(), is_new=False, old_snapshot=old, new_snapshot=new
            )
            mock_send.assert_called_once()

    async def test_no_changes_skip_email(self):
        db = AsyncMock()
        user = MagicMock(
            email="test@example.com",
            full_name="Test User",
            timezone="UTC",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        db.execute.return_value = mock_result

        old = {
            "reminders_enabled": True, "schedule_all": True,
            "global_frequency": "DAILY", "global_time": "09:00:00",
            "tasks_config": {"enabled": True, "frequency": "DAILY", "time": "09:00:00"},
            "meetings_config": {"enabled": False, "frequency": None, "time": None},
            "calendar_config": {"enabled": False, "frequency": None, "time": None},
        }
        new = dict(old)

        with patch("app.modules.reminders.notification_service._send_updated_email", new_callable=AsyncMock) as mock_send:
            await send_reminder_confirmation(
                db, uuid.uuid4(), is_new=False, old_snapshot=old, new_snapshot=new
            )
            mock_send.assert_not_called()


class TestSendCreatedEmail:
    @patch("app.modules.reminders.notification_service.send_html_email")
    @patch("app.modules.reminders.notification_service._get_jinja_env")
    async def test_send_with_modules(self, mock_get_env, mock_send_email):
        mock_env = MagicMock()
        mock_template_html = MagicMock()
        mock_template_html.render.return_value = "<html>Created</html>"
        mock_template_txt = MagicMock()
        mock_template_txt.render.return_value = "Created"
        mock_env.get_template.side_effect = lambda name: {
            "reminder_created.html": mock_template_html,
            "reminder_created.txt": mock_template_txt,
        }[name]
        mock_get_env.return_value = mock_env

        new_snapshot = {
            "reminders_enabled": True,
            "schedule_all": True,
            "global_frequency": "DAILY",
            "global_time": "09:00:00",
            "tasks_config": {"enabled": True, "frequency": "DAILY", "time": "09:00:00"},
            "meetings_config": {"enabled": False, "frequency": None, "time": None},
            "calendar_config": {"enabled": False, "frequency": None, "time": None},
        }

        await _send_created_email("test@example.com", "Test User", new_snapshot, "UTC")
        mock_send_email.delay.assert_called_once()

    @patch("app.modules.reminders.notification_service.send_html_email")
    async def test_send_no_modules_skips(self, mock_send_email):
        new_snapshot = {
            "reminders_enabled": True,
            "schedule_all": False,
            "global_frequency": None,
            "global_time": None,
            "tasks_config": None,
            "meetings_config": None,
            "calendar_config": None,
        }
        await _send_created_email("test@example.com", "Test User", new_snapshot, "UTC")
        mock_send_email.delay.assert_not_called()


class TestSendUpdatedEmail:
    @patch("app.modules.reminders.notification_service.send_html_email")
    @patch("app.modules.reminders.notification_service._get_jinja_env")
    async def test_send_with_changes(self, mock_get_env, mock_send_email):
        mock_env = MagicMock()
        mock_template_html = MagicMock()
        mock_template_html.render.return_value = "<html>Updated</html>"
        mock_template_txt = MagicMock()
        mock_template_txt.render.return_value = "Updated"
        mock_env.get_template.side_effect = lambda name: {
            "reminder_updated.html": mock_template_html,
            "reminder_updated.txt": mock_template_txt,
        }[name]
        mock_get_env.return_value = mock_env

        await _send_updated_email(
            "test@example.com", "Test User",
            modified=[{"name": "Tasks", "previous": "Freq: Daily", "updated": "Freq: Weekly"}],
            disabled=["Meetings"],
            enabled=[{"name": "Calendar", "frequency": "Daily", "time": "09:00 AM", "timezone": "UTC"}],
            timezone_str="UTC",
        )
        mock_send_email.delay.assert_called_once()
