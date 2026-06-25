from typing import AsyncGenerator
from redis.asyncio import ConnectionPool, Redis
from app.core.config import settings

# Global connection pool instance variable
redis_pool = ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=1, # Separating operational session tokens cache on db index 1 (Celery uses 0)
    decode_responses=False # Keeps raw binary byte stream formats intact
)

async def get_redis_client() -> AsyncGenerator[Redis, None]:
    """
    FastAPI dependency yielding an async Redis connection context from the global pool.
    """
    client = Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.close()
