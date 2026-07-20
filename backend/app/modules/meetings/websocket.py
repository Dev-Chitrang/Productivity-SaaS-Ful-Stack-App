import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from uuid import UUID
from typing import Optional
import jwt

from app.core.websocket_manager import ws_connection_manager
from app.core.config import settings
from app.core.logger import logger
from app.modules.meetings.dependencies import get_meetings_service
from app.modules.meetings.service import MeetingService
from app.modules.meetings.enums import ParticipantStatus, MeetingStatus
from app.modules.meetings.constants import WSEvent

router = APIRouter(prefix="/ws/meetings", tags=["Live Meeting Realtime Signaling Hub"])

POLL_INTERVAL = 3.0


async def _safe_cleanup(
    room_id: str,
    connection_id: Optional[str],
    meeting_id: UUID,
    user_id: Optional[UUID],
    guest_name: Optional[str],
    guest_email: Optional[str],
    service: MeetingService,
):
    if connection_id is None:
        return

    try:
        ws_connection_manager.disconnect(room_id, connection_id)
    except Exception as exc:
        logger.error("[meeting_id=%s] [participant_id=%s] cleanup failed: disconnect - %s", room_id, connection_id, exc)

    try:
        participant = await service.disconnect_participant_flow(
            meeting_id, user_id=user_id, guest_email=guest_email
        )
    except Exception as exc:
        logger.error("[meeting_id=%s] [participant_id=%s] cleanup failed: disconnect_participant_flow - %s", room_id, connection_id, exc)
        participant = None

    try:
        await ws_connection_manager.broadcast_to_room(room_id, {
            "event": WSEvent.PARTICIPANT_DISCONNECTED,
            "data": {
                "connection_id": connection_id,
                "user_id": str(user_id) if user_id else None,
                "guest_name": guest_name,
            }
        })
    except Exception as exc:
        logger.error("[meeting_id=%s] [participant_id=%s] cleanup failed: broadcast_to_room - %s", room_id, connection_id, exc)

    if user_id:
        try:
            meeting = await service.get_meeting(meeting_id)
            if meeting.host_id == user_id:
                host_name = await service.repo.get_user_name_by_id(user_id) or "Host"
                await ws_connection_manager.broadcast_to_room(room_id, {
                    "event": WSEvent.HOST_LEFT,
                    "data": {
                        "host_id": str(user_id),
                        "host_name": host_name,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "is_temporary": True,
                    }
                })
        except Exception as exc:
            logger.error("[meeting_id=%s] [participant_id=%s] cleanup failed: host_left broadcast - %s", room_id, connection_id, exc)


@router.websocket("/{meeting_id}")
async def meeting_signaling_endpoint(
    websocket: WebSocket,
    meeting_id: UUID,
    token: Optional[str] = None,
    guest_name: Optional[str] = None,
    guest_email: Optional[str] = None,
    service: MeetingService = Depends(get_meetings_service)
):
    # Accept WebSocket first — before any validation
    await websocket.accept()

    room_id = str(meeting_id)
    connection_id: Optional[str] = None

    logger.info("[meeting_id=%s] connection opened", room_id)

    # Extract user_id from JWT token if present
    user_id = None
    if token:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
            user_id = UUID(payload["sub"])
        except (jwt.PyJWTError, ValueError):
            pass

    try:
        # Validate meeting and create/find participant
        participant = await service.join_meeting_flow(
            meeting_id=meeting_id, user_id=user_id, guest_name=guest_name, guest_email=guest_email
        )

        # Use participant.id as connection ID to guarantee uniqueness (guests may share names)
        connection_id = str(participant.id)

        logger.info("[meeting_id=%s] [participant_id=%s] connection authenticated", room_id, connection_id)

        # If this is a reconnecting DISCONNECTED participant, cancel the pending force-leave
        if participant.status == ParticipantStatus.ADMITTED:
            await service.reconnect_participant(meeting_id, participant.id)

        # CRITICAL: Commit the DB session here to release the PostgreSQL row-level lock
        # acquired by join_meeting_flow (status update, participant creation, etc.).
        # Without this commit, the WebSocket's long-lived session holds the lock on the
        # `meetings` row for the entire connection duration. Any subsequent HTTP request
        # that updates the same row (e.g. POST /meetings/{id}/end) will block until the
        # WebSocket disconnects — causing a 30s Axios timeout on the frontend.
        await service.repo.db.commit()

        # Register in connection manager (with participant metadata for logging)
        meeting = await service.get_meeting(meeting_id)
        await ws_connection_manager.connect(
            room_id,
            connection_id,
            websocket,
            metadata={
                "participant_id": str(participant.id),
                "user_id": str(user_id) if user_id else None,
                "guest_name": guest_name,
                "is_host": user_id is not None and meeting.host_id == user_id,
            },
        )

        logger.info("[meeting_id=%s] [participant_id=%s] participant created", room_id, connection_id)

        is_waiting = participant.status == ParticipantStatus.WAITING
        is_admitted = participant.status == ParticipantStatus.ADMITTED

        if is_waiting:
            await ws_connection_manager.broadcast_to_room(room_id, {
                "event": WSEvent.PARTICIPANT_WAITING,
                "data": {
                    "participant_id": str(participant.id),
                    "connection_id": connection_id,
                    "guest_name": guest_name,
                    "user_id": str(user_id) if user_id else None,
                    "type": participant.participant_type.value,
                }
            })
            await ws_connection_manager.send_personal_message({
                "event": WSEvent.WAITING_ROOM_STATUS,
                "message": "Waiting for host to admit you..."
            }, websocket)
        else:
            await ws_connection_manager.broadcast_to_room(room_id, {
                "event": WSEvent.PARTICIPANT_JOINED,
                "data": {
                    "participant_id": str(participant.id),
                    "participant_status": participant.status.value,
                    "connection_id": connection_id,
                    "guest_name": guest_name,
                    "user_id": str(user_id) if user_id else None,
                    "type": participant.participant_type.value,
                    "is_muted": participant.is_muted,
                }
            }, exclude_connection_id=connection_id)

            # Send self-info so the (re)connecting participant can set myParticipant
            await ws_connection_manager.send_personal_message({
                "event": WSEvent.PARTICIPANT_JOINED,
                "data": {
                    "participant_id": str(participant.id),
                    "participant_status": participant.status.value,
                    "connection_id": connection_id,
                    "guest_name": guest_name,
                    "user_id": str(user_id) if user_id else None,
                    "type": participant.participant_type.value,
                    "is_muted": participant.is_muted,
                }
            }, websocket)

        last_muted_state = participant.is_muted

        while True:
            current_state = await service.repo.get_participant_by_id(participant.id)
            if current_state is None:
                break

            meeting_check = await service.repo.get_meeting_status(meeting_id)
            if meeting_check in (MeetingStatus.ENDED, MeetingStatus.IDLE, MeetingStatus.CANCELLED):
                await ws_connection_manager.send_personal_message({
                    "event": WSEvent.MEETING_ENDED,
                    "message": "The meeting has ended."
                }, websocket)
                await websocket.close(code=4000, reason="Meeting ended")
                break

            if current_state.status == ParticipantStatus.REMOVED:
                await ws_connection_manager.send_personal_message({
                    "event": WSEvent.PARTICIPANT_REMOVED,
                    "message": "You have been removed from the meeting."
                }, websocket)
                await websocket.close(code=4000, reason="Removed by host")
                break

            if current_state.status == ParticipantStatus.REJECTED:
                await ws_connection_manager.send_personal_message({
                    "event": WSEvent.PARTICIPANT_REJECTED,
                    "message": "You have been rejected from the meeting."
                }, websocket)
                await websocket.close(code=4000, reason="Rejected by host")
                break

            # Detect admission transition (host admitted via REST)
            if not is_admitted and current_state.status == ParticipantStatus.ADMITTED:
                is_admitted = True
                await ws_connection_manager.send_personal_message({
                    "event": WSEvent.PARTICIPANT_ADMITTED,
                    "message": "You have been admitted to the meeting."
                }, websocket)
                await ws_connection_manager.broadcast_to_room(room_id, {
                    "event": WSEvent.PARTICIPANT_ADMITTED,
                    "data": {
                        "participant_id": str(participant.id),
                        "connection_id": connection_id,
                        "guest_name": guest_name,
                        "user_id": str(user_id) if user_id else None,
                    }
                }, exclude_connection_id=connection_id)
                logger.info("[meeting_id=%s] [participant_id=%s] participant admitted", room_id, connection_id)

            # Detect mute state changes initiated by host
            if is_admitted and current_state.is_muted != last_muted_state:
                last_muted_state = current_state.is_muted
                await ws_connection_manager.send_personal_message({
                    "event": WSEvent.MUTE_CHANGED,
                    "data": {
                        "participant_id": str(participant.id),
                        "is_muted": current_state.is_muted,
                    }
                }, websocket)

            # Non-blocking receive with timeout to allow polling
            try:
                raw_data = await asyncio.wait_for(websocket.receive_json(), timeout=POLL_INTERVAL)
            except asyncio.TimeoutError:
                continue

            if not is_admitted:
                if raw_data.get("type") == "check_admitted":
                    await ws_connection_manager.send_personal_message({
                        "event": WSEvent.STATUS_CHECK,
                        "status": current_state.status.value
                    }, websocket)
                continue

            event_type = raw_data.get("type")

            # Block signaling if muted by host
            if current_state.is_muted and event_type in ["offer", "ice-candidate"]:
                await ws_connection_manager.send_personal_message({
                    "event": WSEvent.MUTED,
                    "message": "You are muted by the host."
                }, websocket)
                continue

            # Self-mute/unmute via WebSocket
            if event_type == "self_mute":
                await service.repo.update_participant(current_state, {"is_muted": True})
                last_muted_state = True
                await ws_connection_manager.broadcast_to_room(room_id, {
                    "event": WSEvent.MUTE_CHANGED,
                    "data": {
                        "participant_id": str(participant.id),
                        "is_muted": True,
                    }
                })
                continue

            if event_type == "self_unmute":
                await service.repo.update_participant(current_state, {"is_muted": False})
                last_muted_state = False
                await ws_connection_manager.broadcast_to_room(room_id, {
                    "event": WSEvent.MUTE_CHANGED,
                    "data": {
                        "participant_id": str(participant.id),
                        "is_muted": False,
                    }
                })
                continue

            # Screen share events
            if event_type == "request_screen_share":
                try:
                    await service.request_screen_share(meeting_id, participant.id)
                except Exception as e:
                    await ws_connection_manager.send_personal_message({
                        "event": WSEvent.ERROR,
                        "message": str(e)
                    }, websocket)
                    continue
                await ws_connection_manager.broadcast_to_room(room_id, {
                    "event": WSEvent.SCREEN_SHARE_REQUESTED,
                    "data": {
                        "participant_id": str(participant.id),
                        "connection_id": connection_id,
                        "guest_name": participant.guest_name,
                        "user_id": str(participant.user_id) if participant.user_id else None,
                    }
                })
                continue

            if event_type == "screen_share_started":
                try:
                    await service.start_screen_share(meeting_id, participant.id, user_id=user_id, guest_name=guest_name)
                except Exception as e:
                    await ws_connection_manager.send_personal_message({
                        "event": WSEvent.ERROR,
                        "message": str(e)
                    }, websocket)
                    continue
                await ws_connection_manager.broadcast_to_room(room_id, {
                    "event": WSEvent.SCREEN_SHARE_STARTED,
                    "data": {
                        "participant_id": str(participant.id),
                        "connection_id": connection_id,
                        "guest_name": participant.guest_name,
                        "user_id": str(participant.user_id) if participant.user_id else None,
                    }
                })
                continue

            if event_type == "screen_share_stopped":
                try:
                    await service.stop_screen_share(meeting_id, participant.id)
                except Exception as e:
                    await ws_connection_manager.send_personal_message({
                        "event": WSEvent.ERROR,
                        "message": str(e)
                    }, websocket)
                    continue
                await ws_connection_manager.broadcast_to_room(room_id, {
                    "event": WSEvent.SCREEN_SHARE_STOPPED,
                    "data": {
                        "participant_id": str(participant.id),
                        "connection_id": connection_id,
                    }
                })
                continue

            # Relay WebRTC signaling
            target_peer = raw_data.get("target_connection_id")
            payload = raw_data.get("payload")

            signaling_message = {
                "event": event_type,
                "sender_connection_id": connection_id,
                "payload": payload
            }

            if target_peer:
                target_ws = ws_connection_manager.active_rooms.get(room_id, {}).get(target_peer)
                if target_ws:
                    await ws_connection_manager.send_personal_message(signaling_message, target_ws)
            else:
                await ws_connection_manager.broadcast_to_room(room_id, signaling_message, exclude_connection_id=connection_id)

    except WebSocketDisconnect:
        await _safe_cleanup(room_id, connection_id, meeting_id, user_id, guest_name, guest_email, service)
        logger.info("[meeting_id=%s] [participant_id=%s] participant disconnected", room_id, connection_id)

    except asyncio.CancelledError:
        await _safe_cleanup(room_id, connection_id, meeting_id, user_id, guest_name, guest_email, service)
        logger.info("[meeting_id=%s] [participant_id=%s] cleanup complete", room_id, connection_id)

    except Exception as e:
        await _safe_cleanup(room_id, connection_id, meeting_id, user_id, guest_name, guest_email, service)
        try:
            await websocket.close(code=4000, reason=str(e))
        except Exception:
            pass
        logger.error("[meeting_id=%s] [participant_id=%s] cleanup failed", room_id, connection_id)
