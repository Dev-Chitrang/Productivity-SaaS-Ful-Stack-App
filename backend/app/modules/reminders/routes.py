from uuid import UUID
from fastapi import APIRouter, Depends, status
from app.core.database import get_db
from app.modules.meetings.dependencies import get_current_user_id
from app.modules.reminders.repository import ReminderRepository
from app.modules.reminders.service import ReminderService
from app.modules.reminders.controller import ReminderController
from app.modules.reminders.schemas import ReminderSettingUpdate, ReminderSettingResponse

router = APIRouter(prefix="/settings/reminders", tags=["User Preferences Notification Matrix"])

@router.get("", response_model=ReminderSettingResponse)
async def get_reminder_settings_endpoint(
    current_user_id: UUID = Depends(get_current_user_id),
    db = Depends(get_db)
):
    ctrl = ReminderController(ReminderService(ReminderRepository(db)))
    return await ctrl.get_settings(current_user_id)

@router.put("", response_model=ReminderSettingResponse)
async def update_reminder_settings_endpoint(
    payload: ReminderSettingUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db = Depends(get_db)
):
    ctrl = ReminderController(ReminderService(ReminderRepository(db)))
    return await ctrl.update_settings(current_user_id, payload)
