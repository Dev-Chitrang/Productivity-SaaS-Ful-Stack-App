from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings
from app.core.runtime import runtime
from app.core.logger import logger

_engine_kwargs: dict = {
    "echo": settings.ENVIRONMENT == "development",
    "pool_pre_ping": True,
}
_engine_kwargs.update(runtime.db_pool.as_kwargs())

engine = create_async_engine(settings.async_database_url, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

Base = declarative_base()

async def check_database_health() -> None:
    """Verify PostgreSQL connection. Raises on failure."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("PostgreSQL connected")
    except Exception as e:
        logger.error("PostgreSQL connection failed: %s", str(e))
        raise

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
