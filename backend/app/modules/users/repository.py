from typing import Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.user import User

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_profile(self, user: User, full_name: Optional[str] = None, timezone: Optional[str] = None) -> User:
        try:
            if full_name is not None:
                user.full_name = full_name
            if timezone is not None:
                user.timezone = timezone
            self.db.add(user)
            return user
        except Exception:
            await self.db.rollback()
            raise

    async def update_email(self, user: User, new_email: str) -> User:
        try:
            user.email = new_email
            self.db.add(user)
            return user
        except Exception:
            await self.db.rollback()
            raise

    async def update_password(self, user: User, new_password_hash: str) -> User:
        try:
            user.password_hash = new_password_hash
            self.db.add(user)
            return user
        except Exception:
            await self.db.rollback()
            raise

    async def update_profile_image(self, user: User, image_base64: str) -> User:
        try:
            user.profile_image = image_base64
            self.db.add(user)
            return user
        except Exception:
            await self.db.rollback()
            raise

    async def toggle_2fa(self, user: User, enable: bool) -> User:
        try:
            user.is_2fa_enabled = enable
            self.db.add(user)
            return user
        except Exception:
            await self.db.rollback()
            raise

    async def soft_delete(self, user: User) -> None:
        try:
            user.is_active = False
            self.db.add(user)
        except Exception:
            await self.db.rollback()
            raise
