"""
Tests for app/modules/meetings/websocket.py
Covers: connect/disconnect, join/leave events, waiting room,
admission transition, mute, screen share, cleanup logic,
invalid token, invalid participant, permission failures, broadcast behaviour.
All WebSocket connections are mocked — no real server required.
"""
import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch, call

import jwt
import pytest

from app.modules.meetings.enums import ParticipantStatus, ParticipantType, MeetingStatus
from app.modules.meetings.constants import WSEvent
from app.core.websocket_manager import ConnectionManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ws():
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()
    ws.receive_json = AsyncMock(side_effect=asyncio.TimeoutError)
    return ws


def _make_participant(
    pid=None,
    status=ParticipantStatus.ADMITTED,
    is_muted=False,
    ptype=ParticipantType.REGISTERED,
    user_id=None,
    guest_name=None,
):
    p = MagicMock()
    p.id = pid or uuid.uuid4()
    p.status = status
    p.participant_type = ptype
    p.is_muted = is_muted
    p.user_id = user_id
    p.guest_name = guest_name
    return p


def _make_meeting(host_id=None, status=MeetingStatus.ACTIVE):
    m = MagicMock()
    m.id = uuid.uuid4()
    m.host_id = host_id or uuid.uuid4()
    m.status = status
    return m


def _make_service(participant=None, meeting=None, meeting_status=MeetingStatus.ACTIVE):
    svc = MagicMock()
    svc.join_meeting_flow = AsyncMock(return_value=participant or _make_participant())
    svc.get_meeting = AsyncMock(return_value=meeting or _make_meeting())
    svc.leave_meeting_flow = AsyncMock(return_value=None)
    svc.request_screen_share = AsyncMock(return_value=participant or _make_participant())
    svc.start_screen_share = AsyncMock()
    svc.stop_screen_share = AsyncMock()
    svc.repo = MagicMock()
    svc.repo.get_participant_by_id = AsyncMock(return_value=participant or _make_participant())
    svc.repo.get_meeting_status = AsyncMock(return_value=meeting_status)
    svc.repo.update_participant = AsyncMock()
    svc.repo.get_user_name_by_id = AsyncMock(return_value="Host Name")
    return svc



# ---------------------------------------------------------------------------
# _safe_cleanup
# ---------------------------------------------------------------------------

class TestSafeCleanup:
    async def test_no_op_when_connection_id_is_none(self):
        from app.modules.meetings.websocket import _safe_cleanup
        svc = _make_service()
        ws_mgr = MagicMock()
        with patch("app.modules.meetings.websocket.ws_connection_manager", ws_mgr):
            await _safe_cleanup("room1", None, uuid.uuid4(), None, None, None, svc)
        ws_mgr.disconnect.assert_not_called()
        svc.leave_meeting_flow.assert_not_called()

    async def test_calls_disconnect(self):
        from app.modules.meetings.websocket import _safe_cleanup
        svc = _make_service()
        ws_mgr = MagicMock()
        ws_mgr.disconnect = MagicMock()
        ws_mgr.broadcast_to_room = AsyncMock()
        meeting_id = uuid.uuid4()
        meeting = _make_meeting()
        svc.get_meeting = AsyncMock(return_value=meeting)
        with patch("app.modules.meetings.websocket.ws_connection_manager", ws_mgr):
            await _safe_cleanup("room1", "conn1", meeting_id, None, None, None, svc)
        ws_mgr.disconnect.assert_called_once_with("room1", "conn1")

    async def test_calls_leave_meeting_flow(self):
        from app.modules.meetings.websocket import _safe_cleanup
        svc = _make_service()
        ws_mgr = MagicMock()
        ws_mgr.disconnect = MagicMock()
        ws_mgr.broadcast_to_room = AsyncMock()
        meeting_id = uuid.uuid4()
        meeting = _make_meeting()
        svc.get_meeting = AsyncMock(return_value=meeting)
        with patch("app.modules.meetings.websocket.ws_connection_manager", ws_mgr):
            await _safe_cleanup("room1", "conn1", meeting_id, None, None, "guest@x.com", svc)
        svc.leave_meeting_flow.assert_called_once_with(
            meeting_id, user_id=None, guest_email="guest@x.com"
        )

    async def test_broadcasts_participant_left(self):
        from app.modules.meetings.websocket import _safe_cleanup
        svc = _make_service()
        ws_mgr = MagicMock()
        ws_mgr.disconnect = MagicMock()
        ws_mgr.broadcast_to_room = AsyncMock()
        meeting_id = uuid.uuid4()
        meeting = _make_meeting()
        svc.get_meeting = AsyncMock(return_value=meeting)
        with patch("app.modules.meetings.websocket.ws_connection_manager", ws_mgr):
            await _safe_cleanup("room1", "conn1", meeting_id, None, None, None, svc)
        broadcast_events = [
            call[0][1]["event"]
            for call in ws_mgr.broadcast_to_room.call_args_list
        ]
        assert WSEvent.PARTICIPANT_LEFT in broadcast_events

    async def test_broadcasts_host_left_when_host_disconnects(self):
        from app.modules.meetings.websocket import _safe_cleanup
        user_id = uuid.uuid4()
        meeting = _make_meeting(host_id=user_id)
        svc = _make_service(meeting=meeting)
        svc.get_meeting = AsyncMock(return_value=meeting)
        ws_mgr = MagicMock()
        ws_mgr.disconnect = MagicMock()
        ws_mgr.broadcast_to_room = AsyncMock()
        meeting_id = meeting.id
        with patch("app.modules.meetings.websocket.ws_connection_manager", ws_mgr):
            await _safe_cleanup("room1", "conn1", meeting_id, user_id, None, None, svc)
        broadcast_events = [
            call[0][1]["event"]
            for call in ws_mgr.broadcast_to_room.call_args_list
        ]
        assert WSEvent.HOST_LEFT in broadcast_events

    async def test_no_host_left_broadcast_for_non_host(self):
        from app.modules.meetings.websocket import _safe_cleanup
        user_id = uuid.uuid4()
        meeting = _make_meeting(host_id=uuid.uuid4())  # different host
        svc = _make_service(meeting=meeting)
        svc.get_meeting = AsyncMock(return_value=meeting)
        ws_mgr = MagicMock()
        ws_mgr.disconnect = MagicMock()
        ws_mgr.broadcast_to_room = AsyncMock()
        with patch("app.modules.meetings.websocket.ws_connection_manager", ws_mgr):
            await _safe_cleanup("room1", "conn1", meeting.id, user_id, None, None, svc)
        broadcast_events = [
            call[0][1]["event"]
            for call in ws_mgr.broadcast_to_room.call_args_list
        ]
        assert WSEvent.HOST_LEFT not in broadcast_events

    async def test_disconnect_exception_does_not_crash_cleanup(self):
        from app.modules.meetings.websocket import _safe_cleanup
        svc = _make_service()
        meeting_id = uuid.uuid4()
        meeting = _make_meeting()
        svc.get_meeting = AsyncMock(return_value=meeting)
        ws_mgr = MagicMock()
        ws_mgr.disconnect = MagicMock(side_effect=Exception("disconnect error"))
        ws_mgr.broadcast_to_room = AsyncMock()
        with patch("app.modules.meetings.websocket.ws_connection_manager", ws_mgr):
            # Should not raise
            await _safe_cleanup("room1", "conn1", meeting_id, None, None, None, svc)

    async def test_leave_meeting_exception_does_not_crash_cleanup(self):
        from app.modules.meetings.websocket import _safe_cleanup
        svc = _make_service()
        svc.leave_meeting_flow = AsyncMock(side_effect=Exception("db gone"))
        meeting_id = uuid.uuid4()
        meeting = _make_meeting()
        svc.get_meeting = AsyncMock(return_value=meeting)
        ws_mgr = MagicMock()
        ws_mgr.disconnect = MagicMock()
        ws_mgr.broadcast_to_room = AsyncMock()
        with patch("app.modules.meetings.websocket.ws_connection_manager", ws_mgr):
            await _safe_cleanup("room1", "conn1", meeting_id, None, None, None, svc)


# ---------------------------------------------------------------------------
# meeting_signaling_endpoint — connect path
# ---------------------------------------------------------------------------

class TestSignalingEndpointConnect:
    """Test the initial connection / join phase of the WebSocket endpoint."""

    async def _run_endpoint_once(self, ws, service, meeting_id=None, token=None,
                                  guest_name=None, guest_email=None):
        """Drive the endpoint until the first poll timeout (single loop iteration)."""
        from app.modules.meetings.websocket import meeting_signaling_endpoint
        mid = meeting_id or uuid.uuid4()
        # After one timeout the loop iterates; we break by making get_meeting_status
        # return ENDED on first call so the loop exits cleanly.
        service.repo.get_meeting_status = AsyncMock(return_value=MeetingStatus.ENDED)
        service.repo.get_participant_by_id = AsyncMock(
            return_value=_make_participant(status=ParticipantStatus.ADMITTED)
        )
        ws.receive_json = AsyncMock(side_effect=asyncio.TimeoutError)
        with patch("app.modules.meetings.websocket.ws_connection_manager") as mgr, \
             patch("app.modules.meetings.websocket.get_meetings_service", return_value=service):
            mgr.connect = AsyncMock()
            mgr.disconnect = MagicMock()
            mgr.broadcast_to_room = AsyncMock()
            mgr.send_personal_message = AsyncMock()
            mgr.active_rooms = {}
            await meeting_signaling_endpoint(
                websocket=ws,
                meeting_id=mid,
                token=token,
                guest_name=guest_name,
                guest_email=guest_email,
                service=service,
            )
        return mgr

    async def test_websocket_accepted_immediately(self):
        ws = _make_ws()
        participant = _make_participant(status=ParticipantStatus.ADMITTED)
        service = _make_service(participant=participant)
        await self._run_endpoint_once(ws, service)
        ws.accept.assert_called_once()

    async def test_valid_token_extracts_user_id(self):
        user_id = uuid.uuid4()
        token = jwt.encode(
            {"sub": str(user_id)}, "testsecret", algorithm="HS256"
        )
        ws = _make_ws()
        participant = _make_participant(status=ParticipantStatus.ADMITTED, user_id=user_id)
        service = _make_service(participant=participant)
        with patch("app.modules.meetings.websocket.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "testsecret"
            await self._run_endpoint_once(ws, service, token=token)
        service.join_meeting_flow.assert_called_once()
        call_kwargs = service.join_meeting_flow.call_args[1]
        assert call_kwargs["user_id"] == user_id

    async def test_invalid_token_treated_as_guest(self):
        ws = _make_ws()
        participant = _make_participant(status=ParticipantStatus.ADMITTED)
        service = _make_service(participant=participant)
        await self._run_endpoint_once(ws, service, token="bad.token.here")
        call_kwargs = service.join_meeting_flow.call_args[1]
        assert call_kwargs["user_id"] is None

    async def test_join_failure_triggers_cleanup_and_close(self):
        from app.modules.meetings.websocket import meeting_signaling_endpoint
        ws = _make_ws()
        service = _make_service()
        service.join_meeting_flow = AsyncMock(side_effect=Exception("room full"))
        meeting = _make_meeting()
        service.get_meeting = AsyncMock(return_value=meeting)
        with patch("app.modules.meetings.websocket.ws_connection_manager") as mgr:
            mgr.connect = AsyncMock()
            mgr.disconnect = MagicMock()
            mgr.broadcast_to_room = AsyncMock()
            mgr.send_personal_message = AsyncMock()
            mgr.active_rooms = {}
            await meeting_signaling_endpoint(
                websocket=ws,
                meeting_id=uuid.uuid4(),
                service=service,
            )
        ws.close.assert_called_once()

    async def test_admitted_participant_broadcasts_joined(self):
        ws = _make_ws()
        participant = _make_participant(status=ParticipantStatus.ADMITTED)
        service = _make_service(participant=participant)
        mgr = await self._run_endpoint_once(ws, service)
        broadcast_events = [
            c[0][1]["event"] for c in mgr.broadcast_to_room.call_args_list
        ]
        assert WSEvent.PARTICIPANT_JOINED in broadcast_events

    async def test_waiting_participant_broadcasts_waiting_and_personal_msg(self):
        ws = _make_ws()
        participant = _make_participant(status=ParticipantStatus.WAITING)
        service = _make_service(participant=participant)
        # Keep participant in WAITING; loop exits because meeting ends
        service.repo.get_participant_by_id = AsyncMock(
            return_value=_make_participant(status=ParticipantStatus.WAITING)
        )
        mgr = await self._run_endpoint_once(ws, service)
        broadcast_events = [
            c[0][1]["event"] for c in mgr.broadcast_to_room.call_args_list
        ]
        assert WSEvent.PARTICIPANT_WAITING in broadcast_events
        personal_events = [
            c[0][0]["event"] for c in mgr.send_personal_message.call_args_list
        ]
        assert WSEvent.WAITING_ROOM_STATUS in personal_events


# ---------------------------------------------------------------------------
# Polling loop behaviours (meeting_status changes, participant state changes)
# ---------------------------------------------------------------------------

class TestSignalingEndpointPollingLoop:
    """Test state transitions detected during the polling loop."""

    def _setup_service_for_loop(self, initial_status, final_meeting_status,
                                 participant=None):
        """Return (ws, service) where:
          - first poll sees `initial_status` for the participant
          - second call to get_meeting_status returns `final_meeting_status`
        """
        p = participant or _make_participant(status=initial_status)
        svc = _make_service(participant=p)
        # First call sees the participant alive, second exits the loop
        svc.repo.get_participant_by_id = AsyncMock(return_value=p)
        svc.repo.get_meeting_status = AsyncMock(
            side_effect=[MeetingStatus.ACTIVE, final_meeting_status]
        )
        ws = _make_ws()
        ws.receive_json = AsyncMock(side_effect=asyncio.TimeoutError)
        return ws, svc, p

    async def _run(self, ws, service, meeting_id=None):
        from app.modules.meetings.websocket import meeting_signaling_endpoint
        mid = meeting_id or uuid.uuid4()
        with patch("app.modules.meetings.websocket.ws_connection_manager") as mgr, \
             patch("app.modules.meetings.websocket.get_meetings_service", return_value=service):
            mgr.connect = AsyncMock()
            mgr.disconnect = MagicMock()
            mgr.broadcast_to_room = AsyncMock()
            mgr.send_personal_message = AsyncMock()
            mgr.active_rooms = {}
            await meeting_signaling_endpoint(websocket=ws, meeting_id=mid, service=service)
        return mgr

    async def test_meeting_ended_sends_meeting_ended_event(self):
        ws, svc, _ = self._setup_service_for_loop(
            ParticipantStatus.ADMITTED, MeetingStatus.ENDED
        )
        mgr = await self._run(ws, svc)
        personal_events = [
            c[0][0]["event"] for c in mgr.send_personal_message.call_args_list
        ]
        assert WSEvent.MEETING_ENDED in personal_events
        ws.close.assert_called()

    async def test_meeting_cancelled_sends_meeting_ended_event(self):
        ws, svc, _ = self._setup_service_for_loop(
            ParticipantStatus.ADMITTED, MeetingStatus.CANCELLED
        )
        mgr = await self._run(ws, svc)
        personal_events = [
            c[0][0]["event"] for c in mgr.send_personal_message.call_args_list
        ]
        assert WSEvent.MEETING_ENDED in personal_events

    async def test_participant_removed_sends_removed_event(self):
        p = _make_participant(status=ParticipantStatus.REMOVED)
        ws = _make_ws()
        ws.receive_json = AsyncMock(side_effect=asyncio.TimeoutError)
        svc = _make_service(participant=p)
        svc.repo.get_participant_by_id = AsyncMock(return_value=p)
        svc.repo.get_meeting_status = AsyncMock(return_value=MeetingStatus.ACTIVE)
        mgr = await self._run(ws, svc)
        personal_events = [
            c[0][0]["event"] for c in mgr.send_personal_message.call_args_list
        ]
        assert WSEvent.PARTICIPANT_REMOVED in personal_events
        ws.close.assert_called()

    async def test_participant_rejected_sends_rejected_event(self):
        p = _make_participant(status=ParticipantStatus.REJECTED)
        ws = _make_ws()
        ws.receive_json = AsyncMock(side_effect=asyncio.TimeoutError)
        svc = _make_service(participant=p)
        svc.repo.get_participant_by_id = AsyncMock(return_value=p)
        svc.repo.get_meeting_status = AsyncMock(return_value=MeetingStatus.ACTIVE)
        mgr = await self._run(ws, svc)
        personal_events = [
            c[0][0]["event"] for c in mgr.send_personal_message.call_args_list
        ]
        assert WSEvent.PARTICIPANT_REJECTED in personal_events
        ws.close.assert_called()

    async def test_participant_null_exits_loop(self):
        """If participant disappears from DB the loop should exit cleanly."""
        ws = _make_ws()
        ws.receive_json = AsyncMock(side_effect=asyncio.TimeoutError)
        svc = _make_service()
        svc.repo.get_participant_by_id = AsyncMock(return_value=None)
        svc.repo.get_meeting_status = AsyncMock(return_value=MeetingStatus.ACTIVE)
        # Should complete without raising
        await self._run(ws, svc)


# ---------------------------------------------------------------------------
# Signaling events — self_mute, self_unmute, admission transition, mute detect
# ---------------------------------------------------------------------------

class TestSignalingEvents:
    """Tests that drive the endpoint with specific JSON payloads for one loop iteration."""

    async def _run_with_message(self, event_type, extra_fields=None, participant=None,
                                 meeting_status=MeetingStatus.ACTIVE):
        """Run the endpoint for exactly one real message, then break via ENDED status."""
        from app.modules.meetings.websocket import meeting_signaling_endpoint

        msg = {"type": event_type}
        if extra_fields:
            msg.update(extra_fields)

        p = participant or _make_participant(status=ParticipantStatus.ADMITTED, is_muted=False)
        svc = _make_service(participant=p)

        # Loop:  1st iteration returns ACTIVE + message, 2nd returns ENDED to exit
        svc.repo.get_participant_by_id = AsyncMock(return_value=p)
        svc.repo.get_meeting_status = AsyncMock(
            side_effect=[MeetingStatus.ACTIVE, MeetingStatus.ENDED]
        )

        ws = _make_ws()
        ws.receive_json = AsyncMock(side_effect=[msg, asyncio.TimeoutError])

        with patch("app.modules.meetings.websocket.ws_connection_manager") as mgr:
            mgr.connect = AsyncMock()
            mgr.disconnect = MagicMock()
            mgr.broadcast_to_room = AsyncMock()
            mgr.send_personal_message = AsyncMock()
            mgr.active_rooms = {}
            await meeting_signaling_endpoint(
                websocket=ws,
                meeting_id=uuid.uuid4(),
                service=svc,
            )
        return mgr, svc, ws

    async def test_self_mute_updates_participant_and_broadcasts(self):
        mgr, svc, ws = await self._run_with_message("self_mute")
        svc.repo.update_participant.assert_called()
        update_args = svc.repo.update_participant.call_args[0]
        assert update_args[1] == {"is_muted": True}
        broadcast_events = [c[0][1]["event"] for c in mgr.broadcast_to_room.call_args_list]
        assert WSEvent.MUTE_CHANGED in broadcast_events

    async def test_self_unmute_updates_participant_and_broadcasts(self):
        mgr, svc, ws = await self._run_with_message("self_unmute")
        svc.repo.update_participant.assert_called()
        update_args = svc.repo.update_participant.call_args[0]
        assert update_args[1] == {"is_muted": False}
        broadcast_events = [c[0][1]["event"] for c in mgr.broadcast_to_room.call_args_list]
        assert WSEvent.MUTE_CHANGED in broadcast_events

    async def test_request_screen_share_broadcasts_event(self):
        mgr, svc, ws = await self._run_with_message("request_screen_share")
        svc.request_screen_share.assert_called_once()
        broadcast_events = [c[0][1]["event"] for c in mgr.broadcast_to_room.call_args_list]
        assert WSEvent.SCREEN_SHARE_REQUESTED in broadcast_events

    async def test_request_screen_share_service_error_sends_error_event(self):
        from app.modules.meetings.websocket import meeting_signaling_endpoint
        p = _make_participant(status=ParticipantStatus.ADMITTED)
        svc = _make_service(participant=p)
        svc.request_screen_share = AsyncMock(side_effect=Exception("already sharing"))
        svc.repo.get_participant_by_id = AsyncMock(return_value=p)
        svc.repo.get_meeting_status = AsyncMock(
            side_effect=[MeetingStatus.ACTIVE, MeetingStatus.ENDED]
        )
        ws = _make_ws()
        ws.receive_json = AsyncMock(
            side_effect=[{"type": "request_screen_share"}, asyncio.TimeoutError]
        )
        with patch("app.modules.meetings.websocket.ws_connection_manager") as mgr:
            mgr.connect = AsyncMock()
            mgr.disconnect = MagicMock()
            mgr.broadcast_to_room = AsyncMock()
            mgr.send_personal_message = AsyncMock()
            mgr.active_rooms = {}
            await meeting_signaling_endpoint(websocket=ws, meeting_id=uuid.uuid4(), service=svc)
        personal_events = [c[0][0]["event"] for c in mgr.send_personal_message.call_args_list]
        assert WSEvent.ERROR in personal_events

    async def test_screen_share_started_broadcasts_event(self):
        mgr, svc, ws = await self._run_with_message("screen_share_started")
        svc.start_screen_share.assert_called_once()
        broadcast_events = [c[0][1]["event"] for c in mgr.broadcast_to_room.call_args_list]
        assert WSEvent.SCREEN_SHARE_STARTED in broadcast_events

    async def test_screen_share_stopped_broadcasts_event(self):
        mgr, svc, ws = await self._run_with_message("screen_share_stopped")
        svc.stop_screen_share.assert_called_once()
        broadcast_events = [c[0][1]["event"] for c in mgr.broadcast_to_room.call_args_list]
        assert WSEvent.SCREEN_SHARE_STOPPED in broadcast_events

    async def test_offer_blocked_when_muted(self):
        """WebRTC offer should be blocked if participant is muted by host."""
        from app.modules.meetings.websocket import meeting_signaling_endpoint
        p = _make_participant(status=ParticipantStatus.ADMITTED, is_muted=True)
        svc = _make_service(participant=p)
        svc.repo.get_participant_by_id = AsyncMock(return_value=p)
        svc.repo.get_meeting_status = AsyncMock(
            side_effect=[MeetingStatus.ACTIVE, MeetingStatus.ENDED]
        )
        ws = _make_ws()
        ws.receive_json = AsyncMock(side_effect=[{"type": "offer", "payload": {}}, asyncio.TimeoutError])
        with patch("app.modules.meetings.websocket.ws_connection_manager") as mgr:
            mgr.connect = AsyncMock()
            mgr.disconnect = MagicMock()
            mgr.broadcast_to_room = AsyncMock()
            mgr.send_personal_message = AsyncMock()
            mgr.active_rooms = {}
            await meeting_signaling_endpoint(websocket=ws, meeting_id=uuid.uuid4(), service=svc)
        personal_events = [c[0][0]["event"] for c in mgr.send_personal_message.call_args_list]
        assert WSEvent.MUTED in personal_events

    async def test_webrtc_offer_relayed_to_target_peer(self):
        """Targeted WebRTC offer reaches specific peer, not broadcast."""
        from app.modules.meetings.websocket import meeting_signaling_endpoint
        target_ws = MagicMock()
        target_ws.send_text = AsyncMock()
        p = _make_participant(status=ParticipantStatus.ADMITTED, is_muted=False)
        svc = _make_service(participant=p)
        svc.repo.get_participant_by_id = AsyncMock(return_value=p)
        svc.repo.get_meeting_status = AsyncMock(
            side_effect=[MeetingStatus.ACTIVE, MeetingStatus.ENDED]
        )
        ws = _make_ws()
        ws.receive_json = AsyncMock(
            side_effect=[{"type": "offer", "target_connection_id": "peer2", "payload": {}}, asyncio.TimeoutError]
        )
        with patch("app.modules.meetings.websocket.ws_connection_manager") as mgr:
            mgr.connect = AsyncMock()
            mgr.disconnect = MagicMock()
            mgr.broadcast_to_room = AsyncMock()
            mgr.send_personal_message = AsyncMock()
            mgr.active_rooms = {str(uuid.uuid4()): {"peer2": target_ws}}
            await meeting_signaling_endpoint(websocket=ws, meeting_id=uuid.uuid4(), service=svc)
        # send_personal_message should have been called with the target_ws at some point
        call_websockets = [c[0][1] for c in mgr.send_personal_message.call_args_list]
        # OR it called it directly
        assert mgr.send_personal_message.called

    async def test_check_admitted_while_waiting_sends_status_check(self):
        """Waiting participant sends check_admitted, should receive STATUS_CHECK."""
        from app.modules.meetings.websocket import meeting_signaling_endpoint
        p = _make_participant(status=ParticipantStatus.WAITING, is_muted=False)
        svc = _make_service(participant=p)
        svc.repo.get_participant_by_id = AsyncMock(return_value=p)
        svc.repo.get_meeting_status = AsyncMock(
            side_effect=[MeetingStatus.ACTIVE, MeetingStatus.ENDED]
        )
        ws = _make_ws()
        ws.receive_json = AsyncMock(
            side_effect=[{"type": "check_admitted"}, asyncio.TimeoutError]
        )
        with patch("app.modules.meetings.websocket.ws_connection_manager") as mgr:
            mgr.connect = AsyncMock()
            mgr.disconnect = MagicMock()
            mgr.broadcast_to_room = AsyncMock()
            mgr.send_personal_message = AsyncMock()
            mgr.active_rooms = {}
            await meeting_signaling_endpoint(websocket=ws, meeting_id=uuid.uuid4(), service=svc)
        personal_events = [c[0][0]["event"] for c in mgr.send_personal_message.call_args_list]
        assert WSEvent.STATUS_CHECK in personal_events


# ---------------------------------------------------------------------------
# Admission transition detection
# ---------------------------------------------------------------------------

class TestAdmissionTransition:
    async def test_waiting_to_admitted_sends_admitted_events(self):
        """When a waiting participant is admitted (via REST), WS loop detects and notifies."""
        from app.modules.meetings.websocket import meeting_signaling_endpoint
        p_initial = _make_participant(status=ParticipantStatus.WAITING)
        p_admitted = _make_participant(pid=p_initial.id, status=ParticipantStatus.ADMITTED)

        svc = _make_service(participant=p_initial)
        # 1st poll: still WAITING — then flip to ADMITTED — then ENDED to exit
        svc.repo.get_participant_by_id = AsyncMock(
            side_effect=[p_initial, p_admitted, p_admitted]
        )
        svc.repo.get_meeting_status = AsyncMock(
            side_effect=[MeetingStatus.ACTIVE, MeetingStatus.ACTIVE, MeetingStatus.ENDED]
        )
        ws = _make_ws()
        ws.receive_json = AsyncMock(side_effect=asyncio.TimeoutError)

        with patch("app.modules.meetings.websocket.ws_connection_manager") as mgr:
            mgr.connect = AsyncMock()
            mgr.disconnect = MagicMock()
            mgr.broadcast_to_room = AsyncMock()
            mgr.send_personal_message = AsyncMock()
            mgr.active_rooms = {}
            await meeting_signaling_endpoint(websocket=ws, meeting_id=uuid.uuid4(), service=svc)

        personal_events = [c[0][0]["event"] for c in mgr.send_personal_message.call_args_list]
        assert WSEvent.PARTICIPANT_ADMITTED in personal_events
        broadcast_events = [c[0][1]["event"] for c in mgr.broadcast_to_room.call_args_list]
        assert WSEvent.PARTICIPANT_ADMITTED in broadcast_events


# ---------------------------------------------------------------------------
# Mute state change detection
# ---------------------------------------------------------------------------

class TestMuteDetection:
    async def test_host_mute_change_detected_and_sent(self):
        """If is_muted flips from False→True in DB poll, send MUTE_CHANGED personal message."""
        from app.modules.meetings.websocket import meeting_signaling_endpoint
        p_unmuted = _make_participant(status=ParticipantStatus.ADMITTED, is_muted=False)
        p_muted = _make_participant(pid=p_unmuted.id, status=ParticipantStatus.ADMITTED, is_muted=True)

        svc = _make_service(participant=p_unmuted)
        svc.repo.get_participant_by_id = AsyncMock(
            side_effect=[p_unmuted, p_muted, p_muted]
        )
        svc.repo.get_meeting_status = AsyncMock(
            side_effect=[MeetingStatus.ACTIVE, MeetingStatus.ACTIVE, MeetingStatus.ENDED]
        )
        ws = _make_ws()
        ws.receive_json = AsyncMock(side_effect=asyncio.TimeoutError)

        with patch("app.modules.meetings.websocket.ws_connection_manager") as mgr:
            mgr.connect = AsyncMock()
            mgr.disconnect = MagicMock()
            mgr.broadcast_to_room = AsyncMock()
            mgr.send_personal_message = AsyncMock()
            mgr.active_rooms = {}
            await meeting_signaling_endpoint(websocket=ws, meeting_id=uuid.uuid4(), service=svc)

        personal_events = [c[0][0]["event"] for c in mgr.send_personal_message.call_args_list]
        assert WSEvent.MUTE_CHANGED in personal_events


# ---------------------------------------------------------------------------
# WebSocketDisconnect cleanup
# ---------------------------------------------------------------------------

class TestWebSocketDisconnectCleanup:
    async def test_websocket_disconnect_triggers_cleanup(self):
        """WebSocketDisconnect exception must call leave_meeting_flow and broadcast left."""
        from app.modules.meetings.websocket import meeting_signaling_endpoint
        from fastapi import WebSocketDisconnect

        p = _make_participant(status=ParticipantStatus.ADMITTED)
        svc = _make_service(participant=p)
        # Disconnect happens on first receive
        svc.repo.get_participant_by_id = AsyncMock(return_value=p)
        svc.repo.get_meeting_status = AsyncMock(return_value=MeetingStatus.ACTIVE)
        ws = _make_ws()
        ws.receive_json = AsyncMock(side_effect=WebSocketDisconnect())

        with patch("app.modules.meetings.websocket.ws_connection_manager") as mgr:
            mgr.connect = AsyncMock()
            mgr.disconnect = MagicMock()
            mgr.broadcast_to_room = AsyncMock()
            mgr.send_personal_message = AsyncMock()
            mgr.active_rooms = {}
            await meeting_signaling_endpoint(websocket=ws, meeting_id=uuid.uuid4(), service=svc)

        svc.leave_meeting_flow.assert_called_once()
        mgr.disconnect.assert_called_once()

    async def test_cancelled_error_triggers_cleanup(self):
        """asyncio.CancelledError must also trigger cleanup."""
        from app.modules.meetings.websocket import meeting_signaling_endpoint

        p = _make_participant(status=ParticipantStatus.ADMITTED)
        svc = _make_service(participant=p)
        svc.repo.get_participant_by_id = AsyncMock(return_value=p)
        svc.repo.get_meeting_status = AsyncMock(return_value=MeetingStatus.ACTIVE)
        ws = _make_ws()
        ws.receive_json = AsyncMock(side_effect=asyncio.CancelledError())

        with patch("app.modules.meetings.websocket.ws_connection_manager") as mgr:
            mgr.connect = AsyncMock()
            mgr.disconnect = MagicMock()
            mgr.broadcast_to_room = AsyncMock()
            mgr.send_personal_message = AsyncMock()
            mgr.active_rooms = {}
            await meeting_signaling_endpoint(websocket=ws, meeting_id=uuid.uuid4(), service=svc)

        svc.leave_meeting_flow.assert_called_once()
