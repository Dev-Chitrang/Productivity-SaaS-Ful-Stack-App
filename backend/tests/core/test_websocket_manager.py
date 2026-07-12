"""
Tests for app/core/websocket_manager.py
Covers: connect, disconnect, room creation/cleanup, broadcast,
multiple clients, stale connection handling, exclusions.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.websocket_manager import ConnectionManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ws():
    """Return a mock WebSocket with send_text as AsyncMock."""
    ws = MagicMock()
    ws.send_text = AsyncMock()
    return ws


# ---------------------------------------------------------------------------
# connect
# ---------------------------------------------------------------------------

class TestConnect:
    @pytest.fixture
    def manager(self):
        return ConnectionManager()

    async def test_connect_creates_room(self, manager):
        ws = _make_ws()
        await manager.connect("room1", "conn1", ws)
        assert "room1" in manager.active_rooms
        assert "conn1" in manager.active_rooms["room1"]

    async def test_connect_stores_websocket(self, manager):
        ws = _make_ws()
        await manager.connect("room1", "conn1", ws)
        assert manager.active_rooms["room1"]["conn1"] is ws

    async def test_connect_stores_metadata(self, manager):
        ws = _make_ws()
        meta = {"participant_id": "p1", "user_id": "u1", "is_host": True}
        await manager.connect("room1", "conn1", ws, metadata=meta)
        assert manager.connection_meta["room1"]["conn1"] == meta

    async def test_connect_no_metadata_still_registers(self, manager):
        ws = _make_ws()
        await manager.connect("room1", "conn1", ws)
        assert "conn1" in manager.active_rooms["room1"]
        # metadata dict for this conn should not be set
        assert "conn1" not in manager.connection_meta.get("room1", {})

    async def test_connect_multiple_clients_same_room(self, manager):
        ws1, ws2 = _make_ws(), _make_ws()
        await manager.connect("room1", "conn1", ws1)
        await manager.connect("room1", "conn2", ws2)
        assert len(manager.active_rooms["room1"]) == 2

    async def test_connect_multiple_rooms_isolated(self, manager):
        ws1, ws2 = _make_ws(), _make_ws()
        await manager.connect("room1", "conn1", ws1)
        await manager.connect("room2", "conn1", ws2)
        assert manager.active_rooms["room1"]["conn1"] is ws1
        assert manager.active_rooms["room2"]["conn1"] is ws2


# ---------------------------------------------------------------------------
# disconnect
# ---------------------------------------------------------------------------

class TestDisconnect:
    @pytest.fixture
    def manager(self):
        return ConnectionManager()

    async def test_disconnect_removes_connection(self, manager):
        ws = _make_ws()
        await manager.connect("room1", "conn1", ws)
        manager.disconnect("room1", "conn1")
        assert "conn1" not in manager.active_rooms.get("room1", {})

    async def test_disconnect_removes_metadata(self, manager):
        ws = _make_ws()
        await manager.connect("room1", "conn1", ws, metadata={"key": "val"})
        manager.disconnect("room1", "conn1")
        assert "conn1" not in manager.connection_meta.get("room1", {})

    async def test_disconnect_last_client_deletes_room(self, manager):
        ws = _make_ws()
        await manager.connect("room1", "conn1", ws)
        manager.disconnect("room1", "conn1")
        assert "room1" not in manager.active_rooms
        assert "room1" not in manager.connection_meta

    async def test_disconnect_partial_room_preserved(self, manager):
        ws1, ws2 = _make_ws(), _make_ws()
        await manager.connect("room1", "conn1", ws1)
        await manager.connect("room1", "conn2", ws2)
        manager.disconnect("room1", "conn1")
        assert "room1" in manager.active_rooms
        assert "conn2" in manager.active_rooms["room1"]

    async def test_disconnect_nonexistent_connection_no_error(self, manager):
        # Should silently no-op
        manager.disconnect("ghost_room", "ghost_conn")

    async def test_disconnect_nonexistent_room_no_error(self, manager):
        manager.disconnect("unknown", "conn1")

    async def test_disconnect_preserves_other_rooms(self, manager):
        ws1, ws2 = _make_ws(), _make_ws()
        await manager.connect("room1", "conn1", ws1)
        await manager.connect("room2", "conn2", ws2)
        manager.disconnect("room1", "conn1")
        assert "room2" in manager.active_rooms


# ---------------------------------------------------------------------------
# send_personal_message
# ---------------------------------------------------------------------------

class TestSendPersonalMessage:
    @pytest.fixture
    def manager(self):
        return ConnectionManager()

    async def test_sends_json_text(self, manager):
        ws = _make_ws()
        message = {"event": "test", "data": "hello"}
        await manager.send_personal_message(message, ws)
        ws.send_text.assert_called_once()
        sent = ws.send_text.call_args[0][0]
        assert json.loads(sent) == message

    async def test_message_is_json_serialized(self, manager):
        ws = _make_ws()
        await manager.send_personal_message({"event": "x"}, ws)
        call_arg = ws.send_text.call_args[0][0]
        assert isinstance(call_arg, str)
        parsed = json.loads(call_arg)
        assert parsed["event"] == "x"

    async def test_non_serializable_uuid_raises_type_error(self, manager):
        """
        send_personal_message uses json.dumps WITHOUT default=str on the send_text
        call — a UUID in the message raises TypeError.
        NOTE: This exposes a real production bug: the logger call above uses
        default=str (so logging succeeds) but the actual send_text call does not,
        meaning any non-serializable value in a message will crash the send.
        """
        import uuid as _uuid
        ws = _make_ws()
        msg = {"event": "test", "id": _uuid.uuid4()}
        with pytest.raises(TypeError):
            await manager.send_personal_message(msg, ws)

    async def test_serializable_message_does_not_raise(self, manager):
        """Fully JSON-serializable messages work correctly."""
        import uuid as _uuid
        ws = _make_ws()
        msg = {"event": "test", "id": str(_uuid.uuid4())}
        await manager.send_personal_message(msg, ws)
        ws.send_text.assert_called_once()


# ---------------------------------------------------------------------------
# broadcast_to_room
# ---------------------------------------------------------------------------

class TestBroadcastToRoom:
    @pytest.fixture
    def manager(self):
        return ConnectionManager()

    async def test_broadcast_reaches_all_clients(self, manager):
        ws1, ws2 = _make_ws(), _make_ws()
        await manager.connect("room1", "conn1", ws1)
        await manager.connect("room1", "conn2", ws2)
        await manager.broadcast_to_room("room1", {"event": "ping"})
        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()

    async def test_broadcast_respects_exclude(self, manager):
        ws1, ws2 = _make_ws(), _make_ws()
        await manager.connect("room1", "conn1", ws1)
        await manager.connect("room1", "conn2", ws2)
        await manager.broadcast_to_room("room1", {"event": "ping"}, exclude_connection_id="conn1")
        ws1.send_text.assert_not_called()
        ws2.send_text.assert_called_once()

    async def test_broadcast_nonexistent_room_no_error(self, manager):
        # Should silently no-op
        await manager.broadcast_to_room("ghost", {"event": "ping"})

    async def test_broadcast_skips_failed_send(self, manager):
        """A stale WebSocket that raises on send should not crash the broadcast."""
        ws1, ws2 = _make_ws(), _make_ws()
        ws1.send_text = AsyncMock(side_effect=Exception("broken pipe"))
        await manager.connect("room1", "conn1", ws1)
        await manager.connect("room1", "conn2", ws2)
        # Should not raise
        await manager.broadcast_to_room("room1", {"event": "ping"})
        ws2.send_text.assert_called_once()

    async def test_broadcast_sends_correct_payload(self, manager):
        ws = _make_ws()
        await manager.connect("room1", "conn1", ws)
        msg = {"event": "meeting_ended", "data": {"reason": "test"}}
        await manager.broadcast_to_room("room1", msg)
        sent = json.loads(ws.send_text.call_args[0][0])
        assert sent["event"] == "meeting_ended"

    async def test_broadcast_empty_room_after_all_disconnect(self, manager):
        ws = _make_ws()
        await manager.connect("room1", "conn1", ws)
        manager.disconnect("room1", "conn1")
        # room no longer exists; broadcast should be a no-op
        await manager.broadcast_to_room("room1", {"event": "ping"})
        ws.send_text.assert_not_called()

    async def test_broadcast_all_excluded_sends_nothing(self, manager):
        ws = _make_ws()
        await manager.connect("room1", "conn1", ws)
        await manager.broadcast_to_room("room1", {"event": "ping"}, exclude_connection_id="conn1")
        ws.send_text.assert_not_called()


# ---------------------------------------------------------------------------
# Room lifecycle — combined scenarios
# ---------------------------------------------------------------------------

class TestRoomLifecycle:
    @pytest.fixture
    def manager(self):
        return ConnectionManager()

    async def test_room_created_on_first_connect(self, manager):
        ws = _make_ws()
        assert "room1" not in manager.active_rooms
        await manager.connect("room1", "conn1", ws)
        assert "room1" in manager.active_rooms

    async def test_room_destroyed_on_last_disconnect(self, manager):
        ws = _make_ws()
        await manager.connect("room1", "conn1", ws)
        manager.disconnect("room1", "conn1")
        assert "room1" not in manager.active_rooms

    async def test_room_survives_partial_disconnect(self, manager):
        ws1, ws2 = _make_ws(), _make_ws()
        await manager.connect("room1", "conn1", ws1)
        await manager.connect("room1", "conn2", ws2)
        manager.disconnect("room1", "conn1")
        assert "room1" in manager.active_rooms
        assert "conn2" in manager.active_rooms["room1"]

    async def test_reconnect_after_room_destroyed(self, manager):
        ws1, ws2 = _make_ws(), _make_ws()
        await manager.connect("room1", "conn1", ws1)
        manager.disconnect("room1", "conn1")
        # room was destroyed; reconnect should recreate
        await manager.connect("room1", "conn2", ws2)
        assert "room1" in manager.active_rooms
        assert "conn2" in manager.active_rooms["room1"]

    async def test_global_singleton_is_connection_manager(self):
        from app.core.websocket_manager import ws_connection_manager, ConnectionManager
        assert isinstance(ws_connection_manager, ConnectionManager)
