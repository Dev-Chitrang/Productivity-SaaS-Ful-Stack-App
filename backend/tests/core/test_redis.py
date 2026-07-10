import pytest
import os
from unittest.mock import patch, AsyncMock, MagicMock
from app.core.redis import redis_pool, check_redis_health, get_redis_client
from redis.asyncio import ConnectionPool


class TestRedisPool:
    def test_redis_pool_initialized(self):
        assert redis_pool is not None
        assert isinstance(redis_pool, ConnectionPool)

    def test_redis_pool_db_index_1(self):
        assert redis_pool.connection_kwargs.get("db") == 1

    def test_redis_pool_decode_responses_false(self):
        assert redis_pool.connection_kwargs.get("decode_responses") is False


class TestCheckRedisHealth:
    @patch("app.core.redis.Redis")
    async def test_check_redis_health_success(self, mock_redis_cls):
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock()
        mock_client.close = AsyncMock()
        mock_redis_cls.return_value = mock_client

        await check_redis_health()

        mock_client.ping.assert_called_once()
        mock_client.close.assert_called_once()

    @patch("app.core.redis.Redis")
    async def test_check_redis_health_failure(self, mock_redis_cls):
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=Exception("connection refused"))
        mock_client.close = AsyncMock()
        mock_redis_cls.return_value = mock_client

        with pytest.raises(Exception):
            await check_redis_health()

        mock_client.close.assert_called_once()


class TestGetRedisClient:
    @patch("app.core.redis.Redis")
    async def test_get_redis_client_yields_client(self, mock_redis_cls):
        mock_client = AsyncMock()
        mock_client.connection_pool = redis_pool
        mock_redis_cls.return_value = mock_client

        gen = get_redis_client()
        client = await gen.__anext__()
        assert client is mock_client
        assert client.connection_pool is redis_pool
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass

        mock_client.close.assert_called_once()

    @patch("app.core.redis.Redis")
    async def test_get_redis_client_closes_after_yield(self, mock_redis_cls):
        mock_client = AsyncMock()
        mock_client.connection_pool = redis_pool
        mock_redis_cls.return_value = mock_client

        gen = get_redis_client()
        client = await gen.__anext__()
        assert client is mock_client
        assert client.connection_pool is redis_pool
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass

        mock_client.close.assert_called_once()
