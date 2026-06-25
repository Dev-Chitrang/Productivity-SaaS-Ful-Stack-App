from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from uuid6 import uuid7
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid7)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)  # Nullable for OAuth-only users
    full_name = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_2fa_enabled = Column(Boolean, default=False)
    profile_image = Column(Text, nullable=True)
    timezone = Column(String, default="UTC")
    google_id = Column(String, unique=True, nullable=True, index=True)  # Google OAuth subject ID
    oauth_provider = Column(String, nullable=True)  # e.g., 'google', 'password', 'google+password'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
