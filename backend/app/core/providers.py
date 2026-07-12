from app.core.config import settings
from app.core.storage import LocalStorageProvider, S3StorageProvider, StorageProvider, StorageService


def get_storage_provider(subdir: str | None = None) -> StorageProvider:
    if settings.ENVIRONMENT == "PRODUCTION":
        return S3StorageProvider()
    base_dir = settings.STORAGE_BASE_DIR
    if subdir:
        import os
        base_dir = os.path.join(base_dir, subdir)
    return LocalStorageProvider(base_dir)


def get_storage_service(subdir: str | None = None) -> StorageService:
    return StorageService(get_storage_provider(subdir))


def get_email_provider():
    from app.core.email import BrevoEmailProvider, SMTPEmailProvider
    if settings.ENVIRONMENT == "PRODUCTION":
        return BrevoEmailProvider()
    return SMTPEmailProvider()
