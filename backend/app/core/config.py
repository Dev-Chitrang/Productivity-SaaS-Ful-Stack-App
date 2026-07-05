import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "SaaS Productivity Suite"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str

    # PostgreSQL Database Strings
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str
    MEETING_SESSION_TOKEN_EXPIRE_MINUTES: int

    # Redis Configuration
    REDIS_HOST: str
    REDIS_PORT: int

    # Celery Configuration
    REDIS_CELERY_BROKER_URL: str

    # SMTP Configuration
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USE_TLS: bool
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str

    FRONTEND_URL: str

    STORAGE_BASE_DIR: str

    NVIDIA_NIM_API_KEY: str
    NVIDIA_NIM_TIMEOUT: int = 300

    @property
    def async_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def meeting_storage(self) -> str:
        return os.path.join(self.STORAGE_BASE_DIR, "meetings")

    @property
    def transcribe_storage(self) -> str:
        return os.path.join(self.STORAGE_BASE_DIR, "transcribe")

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        valid_envs = ["development", "testing", "production"]
        if v not in valid_envs:
           raise ValueError(f"ENVIRONMENT must be one of {valid_envs}")
        return v

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        extra="ignore"
    )

try:
    settings = Settings()
except Exception as e:
    import sys
    print("CONFIGURATION ERROR: Missing or Invalid essential environment variables.")
    print(e)
    sys.exit(1)

