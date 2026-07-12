import json
import uuid
import secrets
import jwt
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.security import SecurityEngine
from app.modules.auth.service import AuthService
from app.modules.auth.repository import AuthRepository


class TestAuthenticateWithGoogle:
    @pytest.fixture
    def service(self):
        repo = MagicMock(spec=AuthRepository)
        repo.db = AsyncMock()
        redis = AsyncMock()
        return AuthService(repo, redis)

    async def test_verify_token_failure_raises_permission_error(self, service):
        service.repo.get_by_google_id.return_value = None
        with patch(
            "app.modules.auth.service.google_id_token.verify_oauth2_token",
            side_effect=ValueError("invalid token"),
        ), patch.object(SecurityEngine, "generate_auth_tokens") as mock_gen:
            with pytest.raises(PermissionError):
                await service.authenticate_with_google("bad_token")
            mock_gen.assert_not_called()

    async def test_existing_google_user_no_2fa_returns_tokens(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user.email = "user@example.com"
        mock_user.is_2fa_enabled = False
        service.repo.get_by_google_id.return_value = mock_user

        with patch(
            "app.modules.auth.service.google_id_token.verify_oauth2_token",
            return_value={
                "sub": "google_123",
                "email": "user@example.com",
                "name": "User",
                "picture": None,
            },
        ), patch.object(SecurityEngine, "generate_auth_tokens") as mock_gen:
            mock_gen.return_value = {
                "access_token": "acc",
                "refresh_token": "ref",
                "token_type": "bearer",
            }
            result = await service.authenticate_with_google("valid_token")
            assert result["access_token"] == "acc"
            assert result["refresh_token"] == "ref"
            assert result["requires_2fa"] is False
            service.redis.setex.assert_called_once()

    async def test_existing_google_user_with_2fa(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user.email = "user@example.com"
        mock_user.is_2fa_enabled = True
        service.repo.get_by_google_id.return_value = mock_user

        with patch(
            "app.modules.auth.service.google_id_token.verify_oauth2_token",
            return_value={
                "sub": "google_123",
                "email": "user@example.com",
                "name": "User",
                "picture": None,
            },
        ), patch.object(secrets, "choice", return_value="1"), \
            patch("app.modules.auth.service.send_async_email"):
            result = await service.authenticate_with_google("valid_token")
            assert result["requires_2fa"] is True
            assert "verification_token" in result
            service.redis.setex.assert_called()

    async def test_new_google_user_created(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user.email = "new@example.com"
        mock_user.is_2fa_enabled = False
        service.repo.get_by_google_id.return_value = None
        service.repo.get_by_email.return_value = None
        service.repo.create_oauth_user.return_value = mock_user

        with patch(
            "app.modules.auth.service.google_id_token.verify_oauth2_token",
            return_value={
                "sub": "google_new",
                "email": "new@example.com",
                "name": "New User",
                "picture": None,
            },
        ), patch.object(SecurityEngine, "generate_auth_tokens") as mock_gen:
            mock_gen.return_value = {
                "access_token": "acc",
                "refresh_token": "ref",
            }
            result = await service.authenticate_with_google("valid_token")
            assert result["access_token"] == "acc"
            service.repo.create_oauth_user.assert_called_once()
            service.repo.db.flush.assert_called_once()

    async def test_google_links_existing_email_user(self, service):
        existing_user = MagicMock()
        existing_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        existing_user.email = "existing@example.com"
        existing_user.oauth_provider = None
        existing_user.is_2fa_enabled = False
        service.repo.get_by_google_id.return_value = None
        service.repo.get_by_email.return_value = existing_user
        service.repo.link_google_account.return_value = existing_user

        with patch(
            "app.modules.auth.service.google_id_token.verify_oauth2_token",
            return_value={
                "sub": "google_123",
                "email": "existing@example.com",
                "name": "Existing",
                "picture": None,
            },
        ), patch.object(SecurityEngine, "generate_auth_tokens") as mock_gen:
            mock_gen.return_value = {
                "access_token": "acc",
                "refresh_token": "ref",
            }
            result = await service.authenticate_with_google("valid_token")
            service.repo.link_google_account.assert_called_once()
            assert result["access_token"] == "acc"


class TestRegisterUser:
    @pytest.fixture
    def service(self):
        repo = MagicMock(spec=AuthRepository)
        repo.db = AsyncMock()
        redis = AsyncMock()
        return AuthService(repo, redis)

    async def test_register_success(self, service):
        service.repo.get_by_email.return_value = None
        with patch.object(SecurityEngine, "hash_password", return_value="hash"), \
            patch("app.modules.auth.service.send_async_email"):
            token = await service.register_user(
                "new@example.com", "password123", "New User"
            )
        assert isinstance(token, str)
        assert len(token) > 0
        service.repo.create.assert_called_once()
        service.redis.setex.assert_called_once()

    async def test_register_existing_email_raises(self, service):
        service.repo.get_by_email.return_value = MagicMock()
        with pytest.raises(ValueError, match="Identity profile already exists"):
            await service.register_user(
                "existing@example.com", "password123", "User"
            )
        service.repo.create.assert_not_called()


class TestVerifyRegistrationOtp:
    @pytest.fixture
    def service(self):
        repo = MagicMock(spec=AuthRepository)
        repo.db = AsyncMock()
        redis = AsyncMock()
        return AuthService(repo, redis)

    async def test_verify_success(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user.email = "user@example.com"
        service.repo.get_by_email.return_value = mock_user
        service.redis.get.return_value = json.dumps({"email": "user@example.com", "otp": "123456"}).encode()

        with patch.object(SecurityEngine, "generate_auth_tokens") as mock_gen:
            mock_gen.return_value = {
                "access_token": "acc",
                "refresh_token": "ref",
            }
            result = await service.verify_registration_otp("token_abc", "123456")
            assert result["access_token"] == "acc"
            service.repo.mark_user_verified.assert_called_once_with(mock_user)
            service.redis.delete.assert_called_once()

    async def test_verify_invalid_token(self, service):
        service.redis.get.return_value = None
        with pytest.raises(PermissionError):
            await service.verify_registration_otp("bad_token", "123456")

    async def test_verify_wrong_code(self, service):
        service.redis.get.return_value = json.dumps(
            {"email": "user@example.com", "otp": "000000"}
        ).encode()
        with pytest.raises(PermissionError):
            await service.verify_registration_otp("token_abc", "123456")

    async def test_verify_user_not_found(self, service):
        service.redis.get.return_value = json.dumps({"email": "missing@example.com", "otp": "123456"}).encode()
        service.repo.get_by_email.return_value = None
        with pytest.raises(ValueError):
            await service.verify_registration_otp("token_abc", "123456")


class TestResendSignupOtp:
    @pytest.fixture
    def service(self):
        repo = MagicMock(spec=AuthRepository)
        repo.db = AsyncMock()
        redis = AsyncMock()
        return AuthService(repo, redis)

    async def test_resend_success(self, service):
        service.redis.get.return_value = json.dumps(
            {"email": "user@example.com", "otp": "123456"}
        ).encode()
        with patch.object(secrets, "choice", return_value="1"), \
            patch("app.modules.auth.service.send_async_email"):
            await service.resend_signup_otp("token_abc")
        service.redis.setex.assert_called_once()

    async def test_resend_expired_raises(self, service):
        service.redis.get.return_value = None
        with pytest.raises(ValueError):
            await service.resend_signup_otp("expired_token")


class TestLoginStepOne:
    @pytest.fixture
    def service(self):
        repo = MagicMock(spec=AuthRepository)
        repo.db = AsyncMock()
        redis = AsyncMock()
        return AuthService(repo, redis)

    async def test_login_account_not_found(self, service):
        service.repo.get_by_email.return_value = None
        with pytest.raises(PermissionError, match="ACCOUNT_NOT_FOUND"):
            await service.login_step_one("missing@example.com", "password")

    async def test_login_account_inactive(self, service):
        mock_user = MagicMock()
        mock_user.is_active = False
        service.repo.get_by_email.return_value = mock_user
        with pytest.raises(PermissionError, match="ACCOUNT_INACTIVE"):
            await service.login_step_one("user@example.com", "password")

    async def test_login_oauth_account(self, service):
        mock_user = MagicMock()
        mock_user.is_active = True
        mock_user.password_hash = None
        service.repo.get_by_email.return_value = mock_user
        with pytest.raises(PermissionError, match="OAUTH_ACCOUNT"):
            await service.login_step_one("oauth@example.com", "password")

    async def test_login_wrong_password(self, service):
        mock_user = MagicMock()
        mock_user.is_active = True
        mock_user.password_hash = "hash"
        service.repo.get_by_email.return_value = mock_user
        with patch.object(SecurityEngine, "verify_password", return_value=False):
            with pytest.raises(PermissionError, match="WRONG_PASSWORD"):
                await service.login_step_one("user@example.com", "wrong")

    async def test_login_unverified(self, service):
        mock_user = MagicMock()
        mock_user.is_active = True
        mock_user.password_hash = "hash"
        mock_user.is_verified = False
        service.repo.get_by_email.return_value = mock_user
        with patch.object(SecurityEngine, "verify_password", return_value=True):
            with pytest.raises(ValueError, match="ACCOUNT_UNVERIFIED"):
                await service.login_step_one("user@example.com", "password")

    async def test_login_success_no_2fa(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user.email = "user@example.com"
        mock_user.is_active = True
        mock_user.password_hash = "hash"
        mock_user.is_verified = True
        mock_user.is_2fa_enabled = False
        service.repo.get_by_email.return_value = mock_user

        with patch.object(SecurityEngine, "verify_password", return_value=True), patch.object(
            SecurityEngine, "generate_auth_tokens"
        ) as mock_gen:
            mock_gen.return_value = {
                "access_token": "acc",
                "refresh_token": "ref",
            }
            result = await service.login_step_one("user@example.com", "password")
            assert result["requires_2fa"] is False
            assert result["access_token"] == "acc"
            service.redis.setex.assert_called_once()

    async def test_login_success_2fa_required(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user.email = "user@example.com"
        mock_user.is_active = True
        mock_user.password_hash = "hash"
        mock_user.is_verified = True
        mock_user.is_2fa_enabled = True
        service.repo.get_by_email.return_value = mock_user

        with patch.object(SecurityEngine, "verify_password", return_value=True), patch.object(
            secrets, "choice", return_value="1"
        ), patch("app.modules.auth.service.send_async_email"):
            result = await service.login_step_one("user@example.com", "password")
            assert result["requires_2fa"] is True
            assert "verification_token" in result
            service.redis.setex.assert_called_once()


class TestVerifyLoginOtp:
    @pytest.fixture
    def service(self):
        repo = MagicMock(spec=AuthRepository)
        repo.db = AsyncMock()
        redis = AsyncMock()
        return AuthService(repo, redis)

    async def test_verify_success(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_user.email = "user@example.com"
        service.repo.get_by_email.return_value = mock_user
        service.redis.get.return_value = json.dumps(
            {"email": "user@example.com", "otp": "123456"}
        ).encode()

        with patch.object(SecurityEngine, "generate_auth_tokens") as mock_gen:
            mock_gen.return_value = {
                "access_token": "acc",
                "refresh_token": "ref",
            }
            result = await service.verify_login_otp("vtok", "123456")
            assert result["access_token"] == "acc"
            service.redis.delete.assert_called_once()

    async def test_verify_invalid_token(self, service):
        service.redis.get.return_value = None
        with pytest.raises(PermissionError):
            await service.verify_login_otp("bad_token", "123456")

    async def test_verify_wrong_code(self, service):
        service.redis.get.return_value = json.dumps(
            {"email": "user@example.com", "otp": "000000"}
        ).encode()
        with pytest.raises(PermissionError):
            await service.verify_login_otp("vtok", "123456")

    async def test_verify_user_not_found(self, service):
        service.redis.get.return_value = json.dumps({"email": "missing@example.com", "otp": "123456"}).encode()
        service.repo.get_by_email.return_value = None
        with pytest.raises(ValueError):
            await service.verify_login_otp("vtok", "123456")


class TestResendLoginOtp:
    @pytest.fixture
    def service(self):
        repo = MagicMock(spec=AuthRepository)
        repo.db = AsyncMock()
        redis = AsyncMock()
        return AuthService(repo, redis)

    async def test_resend_success(self, service):
        service.redis.get.return_value = json.dumps(
            {"email": "user@example.com", "otp": "123456"}
        ).encode()
        with patch.object(secrets, "choice", return_value="1"), \
            patch("app.modules.auth.service.send_async_email"):
            await service.resend_login_otp("vtok")
        service.redis.setex.assert_called_once()

    async def test_resend_expired_raises(self, service):
        service.redis.get.return_value = None
        with pytest.raises(ValueError):
            await service.resend_login_otp("expired_vtok")


class TestInitiatePasswordReset:
    @pytest.fixture
    def service(self):
        repo = MagicMock(spec=AuthRepository)
        repo.db = AsyncMock()
        redis = AsyncMock()
        return AuthService(repo, redis)

    async def test_initiate_user_found(self, service):
        mock_user = MagicMock()
        service.repo.get_by_email.return_value = mock_user
        with patch("app.modules.auth.service.send_async_email"):
            await service.initiate_password_reset("user@example.com")
        service.redis.setex.assert_called_once()

    async def test_initiate_user_not_found(self, service):
        service.repo.get_by_email.return_value = None
        await service.initiate_password_reset("missing@example.com")
        service.redis.setex.assert_not_called()


class TestExecutePasswordReset:
    @pytest.fixture
    def service(self):
        repo = MagicMock(spec=AuthRepository)
        repo.db = AsyncMock()
        redis = AsyncMock()
        return AuthService(repo, redis)

    async def test_execute_success(self, service):
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        service.repo.get_by_email.return_value = mock_user
        service.redis.get.return_value = b"user@example.com"

        with patch.object(SecurityEngine, "hash_password", return_value="new_hash"):
            await service.execute_password_reset("token_abc", "newpassword123")
            service.repo.update_password.assert_called_once_with(mock_user, "new_hash")
            service.redis.delete.assert_called()

    async def test_execute_invalid_token(self, service):
        service.redis.get.return_value = None
        with pytest.raises(PermissionError):
            await service.execute_password_reset("bad_token", "newpassword123")

    async def test_execute_user_not_found(self, service):
        service.redis.get.return_value = b"missing@example.com"
        service.repo.get_by_email.return_value = None
        with pytest.raises(ValueError):
            await service.execute_password_reset("token_abc", "newpassword123")


class TestRefreshAccessSession:
    @pytest.fixture
    def service(self):
        repo = MagicMock(spec=AuthRepository)
        repo.db = AsyncMock()
        redis = AsyncMock()
        return AuthService(repo, redis)

    async def test_refresh_success(self, service):
        service.redis.get.return_value = b"refresh_token_abc"
        with patch(
            "app.modules.auth.service.jwt.decode",
            return_value={"sub": "user_id_123", "email": "user@example.com"},
        ), patch.object(SecurityEngine, "generate_auth_tokens") as mock_gen:
            mock_gen.return_value = {
                "access_token": "new_acc",
                "refresh_token": "new_ref",
            }
            result = await service.refresh_access_session("refresh_token_abc")
            assert result["access_token"] == "new_acc"
            assert result["refresh_token"] == "new_ref"
            service.redis.setex.assert_called_once()

    async def test_refresh_invalid_token(self, service):
        service.redis.get.return_value = b"refresh_token_abc"
        with patch(
            "app.modules.auth.service.jwt.decode",
            side_effect=jwt.PyJWTError("invalid"),
        ):
            with pytest.raises(PermissionError):
                await service.refresh_access_session("bad_token")

    async def test_refresh_token_not_whitelisted(self, service):
        service.redis.get.return_value = None
        with patch(
            "app.modules.auth.service.jwt.decode",
            return_value={"sub": "user_id_123", "email": "user@example.com"},
        ):
            with pytest.raises(PermissionError):
                await service.refresh_access_session("refresh_token_abc")

    async def test_refresh_token_mismatch(self, service):
        service.redis.get.return_value = b"different_refresh_token"
        with patch(
            "app.modules.auth.service.jwt.decode",
            return_value={"sub": "user_id_123", "email": "user@example.com"},
        ):
            with pytest.raises(PermissionError):
                await service.refresh_access_session("refresh_token_abc")
