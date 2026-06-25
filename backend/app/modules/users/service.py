import uuid
from redis.asyncio import Redis
from app.core.security import SecurityEngine
from app.modules.users.repository import UserRepository
from app.models.user import User

class UserService:
    def __init__(self, repo: UserRepository, redis: Redis):
        self.repo = repo
        self.redis = redis

    async def get_profile(self, user_id: str) -> User:
        uid = uuid.UUID(user_id)
        user = await self.repo.get_by_id(uid)
        if not user:
            raise ValueError("User not found.")
        return user

    async def update_profile(self, user_id: str, full_name: str | None = None, timezone: str | None = None) -> User:
        uid = uuid.UUID(user_id)
        user = await self.repo.get_by_id(uid)
        if not user:
            raise ValueError("User not found.")
        return await self.repo.update_profile(user, full_name, timezone)

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> None:
        uid = uuid.UUID(user_id)
        user = await self.repo.get_by_id(uid)
        if not user:
            raise ValueError("User not found.")
        if not SecurityEngine.verify_password(current_password, user.password_hash):
            raise PermissionError("Current password is incorrect.")

        new_hash = SecurityEngine.hash_password(new_password)
        await self.repo.update_password(user, new_hash)
        await self.redis.delete(f"session:{user.id}")

    async def change_email(self, user_id: str, current_password: str, new_email: str) -> None:
        uid = uuid.UUID(user_id)
        user = await self.repo.get_by_id(uid)
        if not user:
            raise ValueError("User not found.")
        if not SecurityEngine.verify_password(current_password, user.password_hash):
            raise PermissionError("Current password is incorrect.")

        await self.repo.update_email(user, new_email)
        await self.redis.delete(f"session:{user.id}")

    async def update_profile_image(self, user_id: str, image_base64: str) -> User:
        uid = uuid.UUID(user_id)
        user = await self.repo.get_by_id(uid)
        if not user:
            raise ValueError("User not found.")
        return await self.repo.update_profile_image(user, image_base64)

    async def toggle_2fa(self, user_id: str, enable: bool) -> User:
        uid = uuid.UUID(user_id)
        user = await self.repo.get_by_id(uid)
        if not user:
            raise ValueError("User not found.")
        return await self.repo.toggle_2fa(user, enable)

    async def deactivate_account(self, user_id: str) -> None:
        uid = uuid.UUID(user_id)
        user = await self.repo.get_by_id(uid)
        if not user:
            raise ValueError("User not found.")

        await self.repo.soft_delete(user)
        await self.redis.delete(f"session:{user.id}")
