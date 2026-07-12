from uuid import UUID
from app.modules.reminders.repository import ReminderRepository
from app.modules.reminders.schemas import ReminderSettingUpdate
from app.modules.reminders.notification_service import (
    snapshot_settings,
    send_reminder_confirmation,
)
from app.models.reminders import UserReminderSetting

class ReminderService:
    def __init__(self, repo: ReminderRepository):
        self.repo = repo

    async def get_user_settings(self, user_id: UUID) -> UserReminderSetting:
        settings = await self.repo.get_by_user_id(user_id)
        if not settings:
            settings = await self.repo.create_default_settings(user_id)
        return settings

    async def update_user_settings(
        self, user_id: UUID, payload: ReminderSettingUpdate
    ) -> UserReminderSetting:
        existing = await self.repo.get_by_user_id(user_id)
        is_new = existing is None

        old_snapshot = snapshot_settings(existing) if existing else {}

        settings = await self.get_user_settings(user_id)
        pre_snapshot = snapshot_settings(settings) if is_new else old_snapshot

        data = payload.model_dump(exclude_unset=True)
        updated = await self.repo.update_settings(settings, data)

        new_snapshot = snapshot_settings(updated)

        if pre_snapshot != new_snapshot:
            await send_reminder_confirmation(
                self.repo.db, user_id, is_new, pre_snapshot, new_snapshot
            )

        return updated
