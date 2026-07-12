import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.core.database import get_db, AsyncSessionLocal, Base, check_database_health


class TestDatabase:
    @patch("app.core.database.AsyncSessionLocal")
    async def test_get_db_yields_session(self, mock_factory):
        mock_session = AsyncMock()
        mock_factory.return_value.__aenter__.return_value = mock_session
        gen = get_db()
        session = await gen.__anext__()
        assert session == mock_session
        with pytest.raises(StopAsyncIteration):
            await gen.__anext__()

    @patch("app.core.database.AsyncSessionLocal")
    async def test_get_db_rollback_on_error(self, mock_factory):
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_factory.return_value.__aenter__.return_value = mock_session
        gen = get_db()
        await gen.__anext__()
        with pytest.raises(RuntimeError, match="boom"):
            await gen.athrow(RuntimeError("boom"))
        mock_session.rollback.assert_awaited_once()
        mock_session.close.assert_awaited_once()

    def test_base_has_metadata(self):
        assert hasattr(Base, "metadata")

    def test_async_session_local_exists(self):
        assert AsyncSessionLocal is not None

    @patch("app.core.database.engine")
    async def test_check_database_health_success(self, mock_engine):
        mock_conn = AsyncMock()
        mock_engine.connect.return_value.__aenter__.return_value = mock_conn
        await check_database_health()
        mock_conn.execute.assert_awaited_once()

    @patch("app.core.database.engine")
    @patch("app.core.database.logger")
    async def test_check_database_health_failure(self, mock_logger, mock_engine):
        mock_engine.connect.side_effect = Exception("DB down")
        with pytest.raises(Exception, match="DB down"):
            await check_database_health()
        mock_logger.error.assert_called_once()
