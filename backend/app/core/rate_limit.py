import time
import uuid
import jwt
from fastapi import Request, HTTPException, status, Depends
from redis.asyncio import Redis

from app.core.config import settings
from app.core.redis import get_redis_client
from app.core.logger import logger

class RateLimiter:
    def __init__(self, limit: int, window: int, endpoint_name: str):
        self.limit = limit
        self.window = window
        self.endpoint_name = endpoint_name

    async def __call__(self, request: Request, redis: Redis = Depends(get_redis_client)):
        # 1. Identify user / IP
        user_id = None
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            parts = auth_header.split(" ")
            if len(parts) > 1:
                token = parts[1]
                try:
                    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
                    user_id = payload.get("sub")
                except Exception:
                    # If decoding fails, we will fallback to IP limit
                    pass

        identifier = f"user:{user_id}" if user_id else f"ip:{request.client.host if request.client else 'unknown'}"
        key = f"rate_limit:{self.endpoint_name}:{identifier}"

        # 2. Redis sliding window check
        now = time.time()
        clear_before = now - self.window

        try:
            # Use transaction pipeline to ensure atomicity
            async with redis.pipeline(transaction=True) as pipe:
                pipe.zremrangebyscore(key, 0, clear_before)
                pipe.zcard(key)
                pipe.zrange(key, 0, 0, withscores=True)
                results = await pipe.execute()

            removed_count, current_count, oldest_items = results

            if current_count >= self.limit:
                retry_after = 1
                if oldest_items:
                    _, oldest_score = oldest_items[0]
                    retry_after = max(1, int(float(oldest_score) + self.window - now))
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many requests. Please try again in {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)}
                )

            # Record this request
            async with redis.pipeline(transaction=True) as pipe:
                member = f"{now}:{uuid.uuid4()}"
                pipe.zadd(key, {member: now})
                pipe.expire(key, self.window)
                await pipe.execute()

        except HTTPException:
            raise
        except Exception as e:
            # In case Redis is down or has an error, we fail open to avoid complete service disruption
            logger.error(f"Rate limiting error for {key}: {str(e)}")
