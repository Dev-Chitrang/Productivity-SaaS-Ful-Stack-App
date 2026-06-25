from typing import Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.user import User

class AuthRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str, include_inactive: bool = False) -> Optional[User]:
        if include_inactive:
            stmt = select(User).where(User.email == email)
        else:
            stmt = select(User).where(and_(User.email == email, User.is_active == True))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        stmt = select(User).where(and_(User.google_id == google_id, User.is_active == True))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        stmt = select(User).where(and_(User.id == user_id, User.is_active == True))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, email: str, password_hash: Optional[str], full_name: str, is_2fa_enabled: bool = False) -> User:
        try:
            user = User(
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                is_2fa_enabled=is_2fa_enabled
            )
            self.db.add(user)
            return user
        except Exception:
            await self.db.rollback()
            raise

    async def create_oauth_user(
        self,
        email: str,
        full_name: str,
        google_id: str,
        profile_image: Optional[str] = None,
    ) -> User:
        """Creates a new user authenticated exclusively via Google OAuth."""
        try:
            user = User(
                email=email,
                password_hash=None,
                full_name=full_name,
                is_verified=True,
                is_2fa_enabled=False,
                google_id=google_id,
                oauth_provider="google",
                profile_image=profile_image,
            )
            self.db.add(user)
            return user
        except Exception:
            await self.db.rollback()
            raise

    async def link_google_account(self, user: User, google_id: str, profile_image: Optional[str] = None) -> User:
        """Links a Google account to an existing password-based user."""
        try:
            user.google_id = google_id
            # Mark as linked provider; preserve 'password' if already set
            if user.oauth_provider and user.oauth_provider != "google":
                user.oauth_provider = f"{user.oauth_provider}+google"
            else:
                user.oauth_provider = "google+password"
            if profile_image and not user.profile_image:
                user.profile_image = profile_image
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

    async def mark_user_verified(self, user: User) -> User:
        try:
            user.is_verified = True
            self.db.add(user)
            return user
        except Exception:
            await self.db.rollback()
            raise
