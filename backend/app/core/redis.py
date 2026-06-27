from typing import AsyncGenerator
from redis.asyncio import ConnectionPool, Redis
from app.core.config import settings
from app.core.logger import logger

# Global connection pool instance variable
redis_pool = ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=1, # Separating operational session tokens cache on db index 1 (Celery uses 0)
    decode_responses=False # Keeps raw binary byte stream formats intact
)

async def check_redis_health() -> None:
    """Verify Redis connection. Raises on failure."""
    client = Redis(connection_pool=redis_pool)
    try:
        await client.ping()
        logger.info("Redis connected")
    except Exception as e:
        logger.error("Redis connection failed: %s", str(e))
        raise
    finally:
        await client.close()

async def get_redis_client() -> AsyncGenerator[Redis, None]:
    """
    FastAPI dependency yielding an async Redis connection context from the global pool.
    """
    client = Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.close()
