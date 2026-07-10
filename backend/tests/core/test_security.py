import pytest
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from pwdlib.exceptions import UnknownHashError
from app.core.security import SecurityEngine
from app.core.config import settings


class TestHashPassword:
    def test_returns_string(self):
        result = SecurityEngine.hash_password("securepassword123")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_different_passwords_different_hashes(self):
        h1 = SecurityEngine.hash_password("password1")
        h2 = SecurityEngine.hash_password("password2")
        assert h1 != h2

    def test_same_password_different_hashes(self):
        h1 = SecurityEngine.hash_password("samepassword")
        h2 = SecurityEngine.hash_password("samepassword")
        assert h1 != h2

    def test_empty_password(self):
        result = SecurityEngine.hash_password("")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_long_password(self):
        long_pwd = "a" * 72
        result = SecurityEngine.hash_password(long_pwd)
        assert isinstance(result, str)
        assert len(result) > 0


class TestVerifyPassword:
    def test_verify_correct_password(self):
        hashed = SecurityEngine.hash_password("correctpassword")
        assert SecurityEngine.verify_password("correctpassword", hashed) is True

    def test_verify_wrong_password(self):
        hashed = SecurityEngine.hash_password("correctpassword")
        assert SecurityEngine.verify_password("wrongpassword", hashed) is False

    def test_verify_empty_password(self):
        hashed = SecurityEngine.hash_password("password")
        assert SecurityEngine.verify_password("", hashed) is False

    def test_verify_empty_hash(self):
        with pytest.raises(UnknownHashError):
            SecurityEngine.verify_password("password", "")

    def test_verify_invalid_hash_format(self):
        with pytest.raises(UnknownHashError):
            SecurityEngine.verify_password("password", "not-a-real-hash")

    def test_verify_none_hash(self):
        with pytest.raises(TypeError):
            SecurityEngine.verify_password("password", None)


class TestCreateToken:
    def test_returns_string(self):
        token = SecurityEngine.create_token(
            {"sub": "user_id", "email": "user@example.com"},
            timedelta(minutes=15),
            "secret",
        )
        assert isinstance(token, str)

    def test_token_contains_payload(self):
        token = SecurityEngine.create_token(
            {"sub": "user_id", "email": "user@example.com"},
            timedelta(minutes=15),
            "secret",
        )
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])
        assert decoded["sub"] == "user_id"
        assert decoded["email"] == "user@example.com"

    def test_token_has_expiration(self):
        token = SecurityEngine.create_token(
            {"sub": "user_id"},
            timedelta(minutes=15),
            "secret",
        )
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])
        assert "exp" in decoded
        assert decoded["exp"] > 0

    def test_token_expiration_matches_delta(self):
        token = SecurityEngine.create_token(
            {"sub": "user_id"},
            timedelta(minutes=15),
            "secret",
        )
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])
        now = int(datetime.now(timezone.utc).timestamp())
        assert decoded["exp"] <= now + 15 * 60 + 2
        assert decoded["exp"] >= now + 15 * 60 - 2

    def test_different_secrets_produce_different_tokens(self):
        token1 = SecurityEngine.create_token({"sub": "1"}, timedelta(minutes=15), "secret1")
        token2 = SecurityEngine.create_token({"sub": "1"}, timedelta(minutes=15), "secret2")
        assert token1 != token2

    def test_does_not_mutate_original_payload(self):
        original = {"sub": "user_id"}
        SecurityEngine.create_token(original, timedelta(minutes=15), "secret")
        assert original == {"sub": "user_id"}

    def test_rejects_token_signed_with_wrong_secret(self):
        token = SecurityEngine.create_token(
            {"sub": "user_id"}, timedelta(minutes=15), "secret"
        )
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, "wrong_secret", algorithms=["HS256"])


class TestGenerateAuthTokens:
    def test_returns_expected_keys(self):
        tokens = SecurityEngine.generate_auth_tokens("user_123", "user@example.com")
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "token_type" in tokens

    def test_returns_bearer_token_type(self):
        tokens = SecurityEngine.generate_auth_tokens("user_123", "user@example.com")
        assert tokens["token_type"] == "bearer"

    def test_access_token_short_lived(self):
        tokens = SecurityEngine.generate_auth_tokens("user_123", "user@example.com")
        decoded = jwt.decode(tokens["access_token"], settings.JWT_SECRET_KEY, algorithms=["HS256"])
        now = int(datetime.now(timezone.utc).timestamp())
        assert decoded["exp"] <= now + 15 * 60 + 2
        assert decoded["exp"] >= now + 15 * 60 - 2

    def test_refresh_token_long_lived(self):
        tokens = SecurityEngine.generate_auth_tokens("user_123", "user@example.com")
        decoded = jwt.decode(tokens["refresh_token"], settings.JWT_REFRESH_SECRET_KEY, algorithms=["HS256"])
        now = int(datetime.now(timezone.utc).timestamp())
        assert decoded["exp"] <= now + 7 * 24 * 60 * 60 + 2
        assert decoded["exp"] >= now + 7 * 24 * 60 * 60 - 2

    def test_tokens_contain_correct_payload(self):
        tokens = SecurityEngine.generate_auth_tokens("user_123", "user@example.com")
        access_decoded = jwt.decode(tokens["access_token"], settings.JWT_SECRET_KEY, algorithms=["HS256"])
        refresh_decoded = jwt.decode(tokens["refresh_token"], settings.JWT_REFRESH_SECRET_KEY, algorithms=["HS256"])
        assert access_decoded["sub"] == "user_123"
        assert access_decoded["email"] == "user@example.com"
        assert refresh_decoded["sub"] == "user_123"
        assert refresh_decoded["email"] == "user@example.com"

    def test_different_users_produce_different_tokens(self):
        tokens1 = SecurityEngine.generate_auth_tokens("user_1", "user1@example.com")
        tokens2 = SecurityEngine.generate_auth_tokens("user_2", "user2@example.com")
        assert tokens1["access_token"] != tokens2["access_token"]
        assert tokens1["refresh_token"] != tokens2["refresh_token"]
