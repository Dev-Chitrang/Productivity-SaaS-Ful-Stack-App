import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.modules.reminders.service import ReminderService
from app.modules.reminders.repository import ReminderRepository
from app.models.reminders import UserReminderSetting


class TestReminderService:
    @pytest.fixture
    def repo(self):
        mock = AsyncMock(spec=ReminderRepository)
        mock.db = AsyncMock()
        return mock

    @pytest.fixture
    def service(self, repo):
        return ReminderService(repo)

    async def test_get_user_settings_existing(self, service, repo):
        user_id = uuid.uuid4()
        settings = MagicMock(spec=UserReminderSetting)
        repo.get_by_user_id.return_value = settings
        result = await service.get_user_settings(user_id)
        assert result == settings
        repo.create_default_settings.assert_not_called()

    async def test_get_user_settings_create_default(self, service, repo):
        user_id = uuid.uuid4()
        repo.get_by_user_id.return_value = None
        default_settings = MagicMock(spec=UserReminderSetting)
        repo.create_default_settings.return_value = default_settings
        result = await service.get_user_settings(user_id)
        assert result == default_settings
        repo.create_default_settings.assert_called_once_with(user_id)

    async def test_update_user_settings_new(self, service, repo):
        user_id = uuid.uuid4()
        repo.get_by_user_id.return_value = None
        settings = MagicMock(spec=UserReminderSetting)
        settings.reminders_enabled = True
        settings.schedule_all = True
        settings.global_frequency = "DAILY"
        settings.global_time = None
        repo.create_default_settings.return_value = settings

        repo.update_settings.return_value = settings
        payload = MagicMock()
        payload.model_dump.return_value = {"reminders_enabled": True}

        with patch("app.modules.reminders.service.snapshot_settings") as mock_snapshot:
            mock_snapshot.side_effect = [{}, {"reminders_enabled": True}]
            with patch("app.modules.reminders.service.send_reminder_confirmation", new_callable=AsyncMock) as mock_send:
                result = await service.update_user_settings(user_id, payload)
                assert result == settings
                mock_send.assert_called_once()

    async def test_update_user_settings_no_changes(self, service, repo):
        user_id = uuid.uuid4()
        existing = MagicMock(spec=UserReminderSetting)
        repo.get_by_user_id.return_value = existing
        updated = MagicMock(spec=UserReminderSetting)
        repo.update_settings.return_value = updated

        payload = MagicMock()
        payload.model_dump.return_value = {"reminders_enabled": True}

        with patch("app.modules.reminders.service.snapshot_settings") as mock_snapshot:
            mock_snapshot.return_value = {"same": True}
            with patch("app.modules.reminders.service.send_reminder_confirmation", new_callable=AsyncMock) as mock_send:
                result = await service.update_user_settings(user_id, payload)
                assert result == updated
                mock_send.assert_not_called()
