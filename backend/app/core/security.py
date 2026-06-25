from datetime import datetime, timedelta, timezone
from typing import Dict, Any
import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from app.core.config import settings

# Initialize the modern, secure password hash helper
password_hash = PasswordHash((BcryptHasher(),))

class SecurityEngine:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hashes a plain text password safely using modern bcrypt"""
        return password_hash.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifies a plain password against the stored database hash"""
        return password_hash.verify(plain_password, hashed_password)

    @staticmethod
    def create_token(data: dict, expires_delta: timedelta, secret: str) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": int(expire.timestamp())})
        return jwt.encode(to_encode, secret, algorithm="HS256")

    @classmethod
    def generate_auth_tokens(cls, user_id: str, email: str) -> Dict[str, str]:
        payload = {"sub": user_id, "email": email}
        access_token = cls.create_token(payload, timedelta(minutes=15), settings.JWT_SECRET_KEY)
        refresh_token = cls.create_token(payload, timedelta(days=7), settings.JWT_SECRET_KEY)
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
