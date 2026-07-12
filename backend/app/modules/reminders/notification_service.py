import os
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.workers.tasks import send_html_email

logger = logging.getLogger("saas_app")

MODULE_LABELS = {
    "tasks_config": "Tasks",
    "meetings_config": "Meetings",
    "calendar_config": "Calendar",
}

MODULE_CONFIG_KEYS = {"tasks_config", "meetings_config", "calendar_config"}

TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "templates",
    "emails",
)

_env: Optional[Environment] = None


def _get_jinja_env() -> Environment:
    global _env
    if _env is None:
        _env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
    return _env


def _format_time(time_str: Optional[str]) -> str:
    if not time_str:
        return ""
    try:
        parts = time_str.split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        period = "AM" if hour < 12 else "PM"
        if hour == 0:
            hour_12 = 12
        elif hour > 12:
            hour_12 = hour - 12
        else:
            hour_12 = hour
        return f"{hour_12:02d}:{minute:02d} {period}"
    except (ValueError, IndexError):
        return time_str


def _format_frequency(freq: Optional[str]) -> str:
    if not freq:
        return ""
    return freq.capitalize()


def _format_timestamp(dt: Optional[datetime] = None, tz: str = "UTC") -> str:
    dt = dt or datetime.now(timezone.utc)
    return dt.strftime("%d %b %Y %I:%M %p") + f" {tz}"


def _module_display_line(config: dict, timezone_str: str = "") -> str:
    parts = []
    freq = _format_frequency(config.get("frequency"))
    if freq:
        parts.append(f"Frequency: {freq}")
    time_val = _format_time(config.get("time"))
    if time_val:
        parts.append(f"Time: {time_val}")
    if timezone_str:
        parts.append(f"Timezone: {timezone_str}")
    return ", ".join(parts) if parts else "—"


def _build_module_info(
    config: dict, timezone_str: str = ""
) -> dict:
    return {
        "frequency": _format_frequency(config.get("frequency")),
        "time": _format_time(config.get("time")),
        "timezone": timezone_str,
    }


def _get_effective_module_state(cfg_key: str, snapshot: dict) -> dict:
    reminders_enabled = snapshot.get("reminders_enabled", False)
    if not reminders_enabled:
        return {"enabled": False, "frequency": None, "time": None}

    schedule_all = snapshot.get("schedule_all", True)
    if schedule_all:
        return {
            "enabled": True,
            "frequency": snapshot.get("global_frequency"),
            "time": snapshot.get("global_time"),
        }

    cfg = snapshot.get(cfg_key, {}) or {}
    enabled = cfg.get("enabled", False)
    return {
        "enabled": enabled,
        "frequency": cfg.get("frequency") if enabled else None,
        "time": cfg.get("time") if enabled else None,
    }


async def send_reminder_confirmation(
    db: AsyncSession,
    user_id: UUID,
    is_new: bool,
    old_snapshot: dict,
    new_snapshot: dict,
) -> None:
    try:
        stmt = select(User).where(User.id == user_id)
        user = (await db.execute(stmt)).scalar_one_or_none()
        if not user or not user.email:
            logger.warning(
                "Cannot send reminder confirmation: user %s not found or has no email",
                user_id,
            )
            return

        user_name = user.full_name
        recipient = user.email
        timezone_str = user.timezone or "UTC"

        if is_new:
            await _send_created_email(recipient, user_name, new_snapshot, timezone_str)
            return

        modified, disabled, enabled = _compute_changes(old_snapshot, new_snapshot)

        if not modified and not disabled and not enabled:
            logger.info(
                "No actual changes detected for user %s — skipping email", user_id
            )
            return

        await _send_updated_email(
            recipient, user_name, modified, disabled, enabled, timezone_str
        )

    except Exception:
        logger.exception(
            "Failed to send reminder confirmation email for user %s", user_id
        )


def snapshot_settings(settings) -> dict:
    result: dict = {
        "reminders_enabled": settings.reminders_enabled,
        "schedule_all": settings.schedule_all,
        "global_frequency": settings.global_frequency,
        "global_time": (
            settings.global_time.strftime("%H:%M:%S")
            if settings.global_time is not None
            else None
        ),
    }
    for key in MODULE_CONFIG_KEYS:
        val = getattr(settings, key, None) or {}
        result[key] = {
            "enabled": bool(val.get("enabled", False)),
            "frequency": val.get("frequency"),
            "time": val.get("time"),
        }
    return result


def _compute_changes(old: dict, new: dict):
    modified = []
    disabled = []
    enabled = []

    for key in MODULE_CONFIG_KEYS:
        label = MODULE_LABELS.get(key, key)
        old_st = _get_effective_module_state(key, old)
        new_st = _get_effective_module_state(key, new)

        if old_st["enabled"] and not new_st["enabled"]:
            disabled.append(label)
        elif not old_st["enabled"] and new_st["enabled"]:
            enabled.append({
                "name": label,
                "frequency": _format_frequency(new_st["frequency"]),
                "time": _format_time(new_st["time"]),
                "timezone": "",
            })
        elif old_st["enabled"] and new_st["enabled"]:
            if old_st["frequency"] != new_st["frequency"] or old_st["time"] != new_st["time"]:
                modified.append({
                    "name": label,
                    "previous": _module_display_line(old_st),
                    "updated": _module_display_line(new_st),
                })

    return modified, disabled, enabled


async def _send_created_email(
    recipient: str, user_name: str, new_snapshot: dict, timezone_str: str
) -> None:
    modules = []

    for key in MODULE_CONFIG_KEYS:
        st = _get_effective_module_state(key, new_snapshot)
        if not st["enabled"]:
            continue
        info = {
            "frequency": _format_frequency(st["frequency"]),
            "time": _format_time(st["time"]),
            "timezone": timezone_str,
        }
        modules.append({"name": MODULE_LABELS.get(key, key), **info})

    if not modules:
        logger.info(
            "No enabled modules in new settings — skipping creation email"
        )
        return

    now = datetime.now(timezone.utc)
    context = {
        "user_name": user_name,
        "modules": modules,
        "configured_at": _format_timestamp(now, timezone_str),
        "year": now.year,
    }

    env = _get_jinja_env()
    html = env.get_template("reminder_created.html").render(**context)
    text = env.get_template("reminder_created.txt").render(**context)

    send_html_email.delay(recipient, "Reminder Preferences Configured", html, text)
    logger.info("Reminder creation confirmation email sent to %s", recipient)


async def _send_updated_email(
    recipient: str,
    user_name: str,
    modified: list,
    disabled: list,
    enabled: list,
    timezone_str: str,
) -> None:
    now = datetime.now(timezone.utc)
    context = {
        "user_name": user_name,
        "modified_modules": modified,
        "disabled_modules": disabled,
        "enabled_modules": enabled,
        "updated_at": _format_timestamp(now, timezone_str),
        "year": now.year,
    }

    env = _get_jinja_env()
    html = env.get_template("reminder_updated.html").render(**context)
    text = env.get_template("reminder_updated.txt").render(**context)

    send_html_email.delay(recipient, "Reminder Preferences Updated", html, text)
    logger.info("Reminder update confirmation email sent to %s", recipient)
