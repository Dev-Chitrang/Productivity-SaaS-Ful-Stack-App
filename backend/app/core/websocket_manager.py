import json
from typing import Dict, Any, Optional
from fastapi import WebSocket

from app.core.logger import logger

class ConnectionManager:
    def __init__(self):
        # Layout: { room_id: { connection_id: WebSocket } }
        self.active_rooms: Dict[str, Dict[str, WebSocket]] = {}
        # Metadata lookup: { room_id: { connection_id: { metadata dict } } }
        self.connection_meta: Dict[str, Dict[str, dict]] = {}

    async def connect(
        self,
        room_id: str,
        connection_id: str,
        websocket: WebSocket,
        metadata: Optional[dict] = None,
    ):
        """Registers a websocket inside an isolated room context (must be accepted already)."""
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = {}
            self.connection_meta[room_id] = {}
        self.active_rooms[room_id][connection_id] = websocket
        if metadata is not None:
            self.connection_meta[room_id][connection_id] = metadata

        member_ids = list(self.active_rooms[room_id].keys())
        logger.info(
            "[CONNECT] room=%s conn=%s participant_id=%s user_id=%s guest_name=%s is_host=%s | members=%s",
            room_id,
            connection_id,
            (metadata or {}).get("participant_id"),
            (metadata or {}).get("user_id"),
            (metadata or {}).get("guest_name"),
            (metadata or {}).get("is_host"),
            member_ids,
        )

    def disconnect(self, room_id: str, connection_id: str):
        """Cleans up sockets from tracking trees gracefully to prevent leak memory spikes."""
        was_present = room_id in self.active_rooms and connection_id in self.active_rooms[room_id]

        if room_id in self.active_rooms:
            if connection_id in self.active_rooms[room_id]:
                del self.active_rooms[room_id][connection_id]
            if connection_id in self.connection_meta.get(room_id, {}):
                del self.connection_meta[room_id][connection_id]
            remaining = list(self.active_rooms[room_id].keys())
            if not self.active_rooms[room_id]:
                del self.active_rooms[room_id]
                del self.connection_meta[room_id]
                remaining = []

        logger.info(
            "[DISCONNECT] room=%s conn=%s was_present=%s remaining=%s",
            room_id,
            connection_id,
            was_present,
            remaining if was_present else [],
        )

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Sends a direct payload targeted to a specific active socket link."""
        event = message.get("event", "unknown")
        logger.info(
            "[SEND_PERSONAL] event=%s message=%s",
            event,
            json.dumps(message, default=str),
        )
        await websocket.send_text(json.dumps(message))

    async def broadcast_to_room(
        self,
        room_id: str,
        message: dict,
        exclude_connection_id: Optional[str] = None,
    ):
        """Broadcasts text payloads across all active channels listening within a room."""
        event = message.get("event", "unknown")

        if room_id not in self.active_rooms:
            logger.warning(
                "[BROADCAST] room=%s event=%s room NOT FOUND (no connections)",
                room_id,
                event,
            )
            return

        member_ids = list(self.active_rooms[room_id].keys())
        logger.info(
            "[BROADCAST] room=%s event=%s exclude=%s members=%s",
            room_id,
            event,
            exclude_connection_id,
            member_ids,
        )

        payload = json.dumps(message, default=str)
        for conn_id, connection in self.active_rooms[room_id].items():
            if exclude_connection_id and conn_id == exclude_connection_id:
                logger.info(
                    "[BROADCAST] room=%s conn=%s EXCLUDED (exclude=%s)",
                    room_id,
                    conn_id,
                    exclude_connection_id,
                )
                continue

            meta = self.connection_meta.get(room_id, {}).get(conn_id, {})
            logger.info(
                "[BROADCAST] room=%s conn=%s participant_id=%s user_id=%s guest_name=%s is_host=%s -> ATTEMPT SEND",
                room_id,
                conn_id,
                meta.get("participant_id"),
                meta.get("user_id"),
                meta.get("guest_name"),
                meta.get("is_host"),
            )
            try:
                await connection.send_text(payload)
                logger.info(
                    "[BROADCAST] room=%s conn=%s -> SEND OK",
                    room_id,
                    conn_id,
                )
            except Exception as exc:
                logger.warning(
                    "[BROADCAST] room=%s conn=%s -> SEND FAILED: %s",
                    room_id,
                    conn_id,
                    exc,
                )

# Global reusable infrastructure single-instance interface wrapper
ws_connection_manager = ConnectionManager()
