import secrets
import json
import jwt
import uuid
from typing import Optional
from redis.asyncio import Redis
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from app.core.security import SecurityEngine
from app.core.config import settings
from app.modules.auth.repository import AuthRepository
from app.workers.tasks import send_async_email

# Reusable Google transport request object (avoids creating a new HTTP session per call)
_GOOGLE_REQUEST = google_requests.Request()


class AuthService:
    def __init__(self, repo: AuthRepository, redis: Redis):
        self.repo = repo
        self.redis = redis

    # ------------------------------------------------------------------
    # Google OAuth
    # ------------------------------------------------------------------

    async def authenticate_with_google(self, raw_id_token: str) -> dict:
        """
        Verifies a Google ID Token received from the frontend, then either
        creates a new account, links an existing password account, or logs
        in an existing OAuth user.  Respects 2FA if the user has it enabled.
        """
        # 1. Verify token server-side — this validates issuer, audience,
        #    expiry, and cryptographic signature.
        try:
            idinfo = google_id_token.verify_oauth2_token(
                raw_id_token,
                _GOOGLE_REQUEST,
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError as exc:
            # google-auth raises ValueError for any invalid token
            raise PermissionError(f"Google token verification failed: {exc}") from exc

        google_id: str = idinfo["sub"]
        email: str = idinfo["email"].strip().lower()
        full_name: str = idinfo.get("name", "")
        picture: Optional[str] = idinfo.get("picture")

        # 2. Check if a user already exists by Google ID (fastest path)
        user = await self.repo.get_by_google_id(google_id)

        if not user:
            # 3. No user matched by google_id — look up by email
            existing_email_user = await self.repo.get_by_email(email, include_inactive=False)

            if existing_email_user:
                # 3a. A password-based account with the same email exists.
                #     Link Google to it (account merging).
                user = await self.repo.link_google_account(
                    existing_email_user, google_id, picture
                )
            else:
                # 3b. Brand-new user — create an OAuth-only account.
                user = await self.repo.create_oauth_user(
                    email=email,
                    full_name=full_name,
                    google_id=google_id,
                    profile_image=picture,
                )

            # Flush so the user record has an ID before we use it
            await self.repo.db.flush()

        # 4. Handle 2FA challenge, identical to the password login path
        if user.is_2fa_enabled:
            verification_token = str(uuid.uuid4())
            otp_code = "".join(secrets.choice("0123456789") for _ in range(6))
            payload = json.dumps({"email": user.email, "otp": otp_code})
            await self.redis.setex(f"otp:login:{verification_token}", 300, payload)

            send_async_email.delay(
                recipient=user.email,
                subject="Your Account 2FA Workspace Key",
                body=f"Your secure login verification identifier code parameters: {otp_code}",
            )

            return {"requires_2fa": True, "verification_token": verification_token}

        # 5. Issue JWT tokens
        tokens = SecurityEngine.generate_auth_tokens(str(user.id), user.email)
        await self.redis.setex(f"session:{user.id}", 604800, tokens["refresh_token"])
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer",
            "requires_2fa": False,
        }

    # ------------------------------------------------------------------
    # Email / password registration
    # ------------------------------------------------------------------

    async def register_user(self, email: str, plain_pwd: str, name: str, enable_2fa: bool = False) -> str:
        if await self.repo.get_by_email(email, include_inactive=True):
            raise ValueError("Identity profile already exists inside system parameters.")

        hashed = SecurityEngine.hash_password(plain_pwd)
        await self.repo.create(email, hashed, name, enable_2fa)

        verification_token = str(uuid.uuid4())
        otp_code = "".join(secrets.choice("0123456789") for _ in range(6))
        payload = json.dumps({"email": email, "otp": otp_code})
        await self.redis.setex(f"otp:signup:{verification_token}", 600, payload)

        send_async_email.delay(
            recipient=email,
            subject="Verify Your SaaS Productivity Account",
            body=f"Your registration verification code: {otp_code}"
        )

        return verification_token

    async def verify_registration_otp(self, verification_token: str, user_code: str) -> dict:
        redis_key = f"otp:signup:{verification_token}"
        cached = await self.redis.get(redis_key)

        if not cached:
            raise PermissionError("Invalid or expired code initialization context.")

        if isinstance(cached, bytes):
            cached = cached.decode("utf-8")

        data = json.loads(cached)
        if data["otp"] != user_code:
            raise PermissionError("Invalid or expired code initialization context.")

        user = await self.repo.get_by_email(data["email"])
        if not user:
            raise ValueError("Identity profile parameters not found.")

        await self.repo.mark_user_verified(user)
        await self.redis.delete(redis_key)

        tokens = SecurityEngine.generate_auth_tokens(str(user.id), user.email)
        await self.redis.setex(f"session:{user.id}", 604800, tokens["refresh_token"])
        return tokens

    async def resend_signup_otp(self, verification_token: str) -> None:
        redis_key = f"otp:signup:{verification_token}"
        cached = await self.redis.get(redis_key)

        if not cached:
            raise ValueError("Verification session not found or expired.")

        if isinstance(cached, bytes):
            cached = cached.decode("utf-8")

        data = json.loads(cached)

        new_otp = "".join(secrets.choice("0123456789") for _ in range(6))
        data["otp"] = new_otp
        await self.redis.setex(redis_key, 600, json.dumps(data))

        send_async_email.delay(
            recipient=data["email"],
            subject="Verify Your SaaS Productivity Account",
            body=f"Your registration verification code: {new_otp}"
        )

    # ------------------------------------------------------------------
    # Email / password login
    # ------------------------------------------------------------------

    async def login_step_one(self, email: str, plain_pwd: str) -> dict:
        user = await self.repo.get_by_email(email, include_inactive=True)

        if not user:
            raise PermissionError("ACCOUNT_NOT_FOUND")
        if not user.is_active:
            raise PermissionError("ACCOUNT_INACTIVE")
        if not user.password_hash:
            raise PermissionError("OAUTH_ACCOUNT")
        if not SecurityEngine.verify_password(plain_pwd, user.password_hash):
            raise PermissionError("WRONG_PASSWORD")
        if not user.is_verified:
            raise ValueError("ACCOUNT_UNVERIFIED")

        if not user.is_2fa_enabled:
            tokens = SecurityEngine.generate_auth_tokens(str(user.id), user.email)
            await self.redis.setex(f"session:{user.id}", 604800, tokens["refresh_token"])
            return {"access_token": tokens["access_token"], "refresh_token": tokens["refresh_token"], "token_type": "bearer", "requires_2fa": False}

        verification_token = str(uuid.uuid4())
        otp_code = "".join(secrets.choice("0123456789") for _ in range(6))
        payload = json.dumps({"email": email, "otp": otp_code})
        await self.redis.setex(f"otp:login:{verification_token}", 300, payload)

        send_async_email.delay(
            recipient=email,
            subject="Your Account 2FA Workspace Key",
            body=f"Your secure login verification identifier code parameters: {otp_code}"
        )

        return {"requires_2fa": True, "verification_token": verification_token}

    async def verify_login_otp(self, verification_token: str, code: str) -> dict:
        redis_key = f"otp:login:{verification_token}"
        cached = await self.redis.get(redis_key)

        if not cached:
            raise PermissionError("Invalid or expired multi-factor evaluation token.")

        if isinstance(cached, bytes):
            cached = cached.decode("utf-8")

        data = json.loads(cached)
        if data["otp"] != code:
            raise PermissionError("Invalid or expired multi-factor evaluation token.")

        await self.redis.delete(redis_key)

        user = await self.repo.get_by_email(data["email"])
        if not user:
            raise ValueError("Identity profile parameters not found.")

        tokens = SecurityEngine.generate_auth_tokens(str(user.id), user.email)
        await self.redis.setex(f"session:{user.id}", 604800, tokens["refresh_token"])
        return tokens

    async def resend_login_otp(self, verification_token: str) -> None:
        redis_key = f"otp:login:{verification_token}"
        cached = await self.redis.get(redis_key)

        if not cached:
            raise ValueError("Login verification session not found or expired.")

        if isinstance(cached, bytes):
            cached = cached.decode("utf-8")

        data = json.loads(cached)

        new_otp = "".join(secrets.choice("0123456789") for _ in range(6))
        data["otp"] = new_otp
        await self.redis.setex(redis_key, 300, json.dumps(data))

        send_async_email.delay(
            recipient=data["email"],
            subject="Your Account 2FA Workspace Key",
            body=f"Your secure login verification identifier code parameters: {new_otp}"
        )

    # ------------------------------------------------------------------
    # Password reset
    # ------------------------------------------------------------------

    async def initiate_password_reset(self, email: str) -> None:
        user = await self.repo.get_by_email(email)
        if not user:
            return

        reset_token = secrets.token_urlsafe(32)
        await self.redis.setex(f"reset:{reset_token}", 900, email)

        send_async_email.delay(
            recipient=email,
            subject="Reset Your Account Password Signature",
            body=f"Pass this token parameter to verify modifications: {reset_token}"
        )

    async def execute_password_reset(self, token: str, new_pwd: str) -> None:
        email_bytes = await self.redis.get(f"reset:{token}")
        if not email_bytes:
            raise PermissionError("Reset parameters matching configuration are missing or expired.")

        email = email_bytes.decode("utf-8")
        user = await self.repo.get_by_email(email)
        if not user:
            raise ValueError("Target user profile missing.")

        new_hash = SecurityEngine.hash_password(new_pwd)
        await self.repo.update_password(user, new_hash)

        await self.redis.delete(f"reset:{token}")
        await self.redis.delete(f"session:{user.id}")

    # ------------------------------------------------------------------
    # Token refresh
    # ------------------------------------------------------------------

    async def refresh_access_session(self, refresh_token: str) -> dict:
        try:
            payload = jwt.decode(refresh_token, settings.JWT_REFRESH_SECRET_KEY, algorithms=["HS256"])
            user_id, email = payload["sub"], payload["email"]
        except jwt.PyJWTError:
            raise PermissionError("Session validation has failed or expired.")

        whitelist_token = await self.redis.get(f"session:{user_id}")
        if not whitelist_token or whitelist_token.decode("utf-8") != refresh_token:
            raise PermissionError("Active session validation context tracking revoked.")

        new_tokens = SecurityEngine.generate_auth_tokens(user_id, email)
        await self.redis.setex(f"session:{user_id}", 604800, new_tokens["refresh_token"])
        return new_tokens
