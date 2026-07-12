from uuid import UUID
from app.modules.reminders.service import ReminderService
from app.modules.reminders.schemas import ReminderSettingUpdate, ReminderSettingResponse

class ReminderController:
    def __init__(self, service: ReminderService):
        self.service = service

    async def get_settings(self, user_id: UUID) -> dict:
        settings = await self.service.get_user_settings(user_id)
        return ReminderSettingResponse.model_validate(settings)

    async def update_settings(self, user_id: UUID, payload: ReminderSettingUpdate) -> dict:
        settings = await self.service.update_user_settings(user_id, payload)
        return ReminderSettingResponse.model_validate(settings)
