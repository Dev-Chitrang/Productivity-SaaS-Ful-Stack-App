import pytest
import time
import uuid
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException, Request
from app.core.rate_limit import RateLimiter
from redis.asyncio import Redis


@pytest.fixture
def mock_redis():
    return AsyncMock(spec=Redis)


@pytest.fixture
def mock_request():
    req = MagicMock(spec=Request)
    req.headers = {}
    req.client = MagicMock()
    req.client.host = "127.0.0.1"
    return req


class TestRateLimiter:
    async def test_allows_first_request(self, mock_redis, mock_request):
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipeline
        mock_pipeline.zremrangebyscore = MagicMock()
        mock_pipeline.zcard = MagicMock(return_value=0)
        mock_pipeline.zrange = MagicMock(return_value=[])
        mock_pipeline.zadd = MagicMock()
        mock_pipeline.expire = MagicMock()
        mock_pipeline.execute = AsyncMock(return_value=[0, 0, []])

        limiter = RateLimiter(limit=3, window=60, endpoint_name="auth")
        await limiter(mock_request, mock_redis)
        mock_pipeline.zadd.assert_called_once()

    async def test_blocks_after_limit_exceeded(self, mock_redis, mock_request):
        now = time.time()
        oldest_timestamp = now - 1
        member = f"{oldest_timestamp}:{uuid.uuid4()}"

        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipeline
        mock_pipeline.zremrangebyscore = MagicMock()
        mock_pipeline.zcard = MagicMock(return_value=3)
        mock_pipeline.zrange = MagicMock(return_value=[(member.encode(), oldest_timestamp)])
        mock_pipeline.zadd = MagicMock()
        mock_pipeline.expire = MagicMock()
        mock_pipeline.execute = AsyncMock(return_value=[0, 3, [(member.encode(), oldest_timestamp)]])

        limiter = RateLimiter(limit=3, window=60, endpoint_name="auth")
        with pytest.raises(HTTPException) as exc_info:
            await limiter(mock_request, mock_redis)
        assert exc_info.value.status_code == 429

    async def test_fails_open_when_redis_errors(self, mock_redis, mock_request):
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipeline
        mock_pipeline.zremrangebyscore = MagicMock()
        mock_pipeline.zcard = MagicMock(side_effect=Exception("redis down"))
        mock_pipeline.zrange = MagicMock()
        mock_pipeline.zadd = MagicMock()
        mock_pipeline.expire = MagicMock()
        mock_pipeline.execute = AsyncMock()

        limiter = RateLimiter(limit=3, window=60, endpoint_name="auth")
        result = await limiter(mock_request, mock_redis)
        assert result is None

    async def test_allows_request_under_limit(self, mock_redis, mock_request):
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipeline
        mock_pipeline.zremrangebyscore = MagicMock()
        mock_pipeline.zcard = MagicMock(return_value=2)
        mock_pipeline.zrange = MagicMock(return_value=[])
        mock_pipeline.zadd = MagicMock()
        mock_pipeline.expire = MagicMock()
        mock_pipeline.execute = AsyncMock(return_value=[0, 2, []])

        limiter = RateLimiter(limit=3, window=60, endpoint_name="auth")
        await limiter(mock_request, mock_redis)
        mock_pipeline.zadd.assert_called_once()
