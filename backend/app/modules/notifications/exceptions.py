from uuid import UUID


class NotificationNotFoundException(Exception):
    def __init__(self, notification_id: UUID):
        self.notification_id = notification_id
        super().__init__(f"Notification {notification_id} not found")


class NotificationAccessDeniedException(Exception):
    def __init__(self, notification_id: UUID, user_id: UUID):
        self.notification_id = notification_id
        self.user_id = user_id
        super().__init__(f"User {user_id} denied access to notification {notification_id}")


class SubscriptionNotFoundException(Exception):
    def __init__(self, subscription_id: UUID):
        self.subscription_id = subscription_id
        super().__init__(f"Subscription {subscription_id} not found")


class PushDeliveryException(Exception):
    def __init__(self, user_id: UUID, reason: str):
        self.user_id = user_id
        self.reason = reason
        super().__init__(f"Push delivery failed for user {user_id}: {reason}")
