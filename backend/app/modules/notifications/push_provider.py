import json
import logging
from typing import Optional
from uuid import UUID

from pywebpush import webpush, WebPushException

from app.core.config import settings

logger = logging.getLogger("saas_app")


class PushNotificationProvider:
    VAPID_CLAIMS = {
        "sub": f"mailto:{settings.SMTP_FROM_EMAIL}",
    }

    def __init__(self):
        self._vapid_private_key = getattr(settings, "VAPID_PRIVATE_KEY", "")
        self._vapid_claims = self.VAPID_CLAIMS

    def send_push(self, subscription_info: dict, title: str, body: str, url: Optional[str] = None) -> bool:
        payload = json.dumps({
            "title": title,
            "body": body,
            "url": url or "/dashboard",
        })

        try:
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=self._vapid_private_key,
                vapid_claims=self._vapid_claims,
            )
            return True
        except WebPushException as e:
            logger.warning("Push notification delivery failed: %s", str(e))
            if "404" in str(e) or "410" in str(e):
                logger.info("Subscription expired or invalid, will be cleaned up")
                raise PushSubscriptionExpiredException(subscription_info.get("endpoint", ""))
            return False
        except Exception as e:
            logger.error("Unexpected push notification error: %s", str(e))
            return False


class PushSubscriptionExpiredException(Exception):
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        super().__init__(f"Push subscription expired: {endpoint}")
