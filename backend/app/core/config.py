import os
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"
)

_VALID_ENVIRONMENTS = frozenset({"LOCAL", "PRODUCTION", "TESTING"})


# ---------------------------------------------------------------------------
# Base — shared by every environment
# ---------------------------------------------------------------------------

class BaseAppSettings(BaseSettings):
    """Fields common to every deployment target."""

    PROJECT_NAME: str = "SaaS Productivity Suite"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str
    MEETING_SESSION_TOKEN_EXPIRE_MINUTES: int

    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    @field_validator("ENVIRONMENT")
    @classmethod
    def _validate_environment(cls, v: str) -> str:
        if v not in _VALID_ENVIRONMENTS:
            raise ValueError(
                f"ENVIRONMENT must be one of {sorted(_VALID_ENVIRONMENTS)}"
            )
        return v


# ---------------------------------------------------------------------------
# LOCAL / PRODUCTION — every infrastructure field is required
# ---------------------------------------------------------------------------

class _InfraSettings(BaseAppSettings):
    """Base for environments that require live infrastructure connections.

    Every field here is mandatory (no defaults) — identical to the legacy
    monolithic ``Settings`` class.
    """

    # PostgreSQL
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int

    # Celery
    REDIS_CELERY_BROKER_URL: str

    # SMTP (used by SMTPEmailProvider in LOCAL)
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USE_TLS: bool
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str

    # Google OAuth
    GOOGLE_CLIENT_ID: str

    # App
    FRONTEND_URL: str
    STORAGE_BASE_DIR: str

    # NVIDIA
    NVIDIA_NIM_API_KEY: str
    NVIDIA_NIM_TIMEOUT: int = 300

    # VAPID (Web Push)
    VAPID_PRIVATE_KEY: str = ""
    VAPID_PUBLIC_KEY: str = ""

    # Brevo / SendinBlue (used by BrevoEmailProvider in PRODUCTION)
    BREVO_API_KEY: str = ""
    BREVO_FROM_EMAIL: str = ""

    # AWS S3 (used by S3StorageProvider in PRODUCTION)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = ""
    AWS_STORAGE_BUCKET_NAME: str = ""

    @property
    def async_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def meeting_storage(self) -> str:
        return os.path.join(self.STORAGE_BASE_DIR, "meetings")

    @property
    def transcribe_storage(self) -> str:
        return os.path.join(self.STORAGE_BASE_DIR, "transcribe")

    @property
    def attachment_storage(self) -> str:
        return os.path.join(self.STORAGE_BASE_DIR, "attachments")


class LocalSettings(_InfraSettings):
    """LOCAL development — identical validation to the legacy monolithic Settings."""
    pass


class ProductionSettings(_InfraSettings):
    """PRODUCTION — identical validation to the legacy monolithic Settings."""
    pass


# ---------------------------------------------------------------------------
# TESTING — every field carries a safe default; no real infrastructure required
# ---------------------------------------------------------------------------

class TestingSettings(BaseAppSettings):
    """TESTING — first-class environment with zero infrastructure dependencies.

    Every field that is *required* in LOCAL / PRODUCTION has a safe dummy
    default here so that tests can run without PostgreSQL, Redis, AWS, Brevo,
    SMTP, Google OAuth, NVIDIA, or Storage being available.

    Module-level globals (``engine``, ``redis_pool``) are still *created* at
    import time — but they are never connected because the DI layer is
    overridden in tests.
    """

    __test__ = False  # prevent pytest from treating this as a test class

    MEETING_SESSION_TOKEN_EXPIRE_MINUTES: int = 60

    # PostgreSQL (dummy — engine is created at import time but never connected)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "test"
    POSTGRES_PASSWORD: str = "test"
    POSTGRES_DB: str = "test"

    # JWT
    JWT_SECRET_KEY: str = "test-jwt-secret"
    JWT_REFRESH_SECRET_KEY: str = "test-jwt-refresh-secret"

    # Redis (dummy — pool is created at import time but never connected)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_CELERY_BROKER_URL: str = "redis://localhost:6379/0"

    # SMTP (dummy)
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USE_TLS: bool = False
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str = "test@test.com"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = "test-client-id"

    # App
    FRONTEND_URL: str = "http://localhost:5173"
    STORAGE_BASE_DIR: str = "/tmp/test-storage"

    # NVIDIA
    NVIDIA_NIM_API_KEY: str = "test-api-key"
    NVIDIA_NIM_TIMEOUT: int = 300

    # VAPID
    VAPID_PRIVATE_KEY: str = ""
    VAPID_PUBLIC_KEY: str = ""

    # Brevo
    BREVO_API_KEY: str = ""
    BREVO_FROM_EMAIL: str = ""

    # AWS
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = ""
    AWS_STORAGE_BUCKET_NAME: str = ""

    @property
    def async_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def meeting_storage(self) -> str:
        return os.path.join(self.STORAGE_BASE_DIR, "meetings")

    @property
    def transcribe_storage(self) -> str:
        return os.path.join(self.STORAGE_BASE_DIR, "transcribe")

    @property
    def attachment_storage(self) -> str:
        return os.path.join(self.STORAGE_BASE_DIR, "attachments")


# ---------------------------------------------------------------------------
# Factory — ENVIRONMENT selects the concrete implementation
# ---------------------------------------------------------------------------

_ENV_SETTINGS_MAP: dict[str, type[BaseAppSettings]] = {
    "LOCAL": LocalSettings,
    "PRODUCTION": ProductionSettings,
    "TESTING": TestingSettings,
}


class _EnvironmentDetector(BaseSettings):
    """Minimal reader used only to discover ENVIRONMENT before the real settings."""
    ENVIRONMENT: str = ""
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")


def _build_settings() -> BaseAppSettings:
    env = _EnvironmentDetector().ENVIRONMENT
    if env not in _ENV_SETTINGS_MAP:
        raise ValueError(
            f"ENVIRONMENT must be one of {sorted(_ENV_SETTINGS_MAP)}, got '{env}'"
        )
    return _ENV_SETTINGS_MAP[env]()


# Backward-compatible alias — code that does
# ``from app.core.config import Settings`` and uses it as a type
# (e.g. ``MagicMock(spec=Settings)``) gets LocalSettings, which carries
# the full set of fields.
Settings = LocalSettings


try:
    settings = _build_settings()
except Exception as e:
    import sys
    print("CONFIGURATION ERROR: Missing or Invalid essential environment variables.")
    print(e)
    sys.exit(1)
