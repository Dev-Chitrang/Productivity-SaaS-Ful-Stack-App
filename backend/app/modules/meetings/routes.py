from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status, UploadFile, File, Form, HTTPException, Body
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from app.core.websocket_manager import ws_connection_manager
from app.modules.meetings.dependencies import get_current_user_id, get_optional_user_id, get_meetings_service, get_attachment_service
from app.modules.meetings.controller import MeetingController, MeetingAIAnalysisController, SessionHistoryController
from app.modules.meetings.repository import MeetingAIAnalysisRepository
from app.modules.meetings.ai_provider_service import AIProviderService
from app.modules.meetings.schemas import (
    MeetingCreate, MeetingUpdate, MeetingResponse,
    MeetingParticipantResponse, MeetingJoinPayload,
    MeetingJoinInfoResponse, MeetingJoinResponse, RecordingResponse, TranscriptResponse,
    WaitingCountResponse, ScheduledMeetingCreate, ScheduledMeetingUpdate, InvitationCreate, InvitationResponse, AIAnalysisResponse, AIAnalysisStatusResponse, AIAnalysisPayloadSchema, AIAnalysisStatus,
    SessionHistoryItemResponse, SessionDetailResponse,
    RecentAIAnalysisItem,
)
from app.modules.meetings.enums import ParticipantStatus
from app.modules.meetings.constants import WSEvent
from app.modules.meetings.exceptions import (
    MeetingNotFoundException,
    MeetingAccessDeniedException,
    MeetingValidationError,
    SessionAccessDeniedException,
)
from app.modules.meetings.service import MeetingAIAnalysisService
from app.modules.attachments.enums import AttachmentEntityType
from app.modules.attachments.exceptions import (
    AttachmentNotFoundException,
    AttachmentStorageError,
    AttachmentValidationError,
)
from app.modules.attachments.schemas import AttachmentListResponse, AttachmentResponse
from app.modules.attachments.service import AttachmentService

router = APIRouter(prefix="/meetings", tags=["Transactional Live Video Signaling Engine"])


meeting_analysis_router = APIRouter(prefix="/meetings/{meeting_id}/analysis", tags=["Asynchronous Meeting AI Insights"])

@router.post("", status_code=status.HTTP_201_CREATED, response_model=MeetingResponse)
async def create_meeting_endpoint(
    payload: MeetingCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    return await ctrl.create_meeting(current_user_id, payload)

@router.get("", status_code=status.HTTP_200_OK, response_model=List[MeetingResponse])
async def list_meetings_endpoint(
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    return await ctrl.list_user_meetings(current_user_id)

@router.get("/by-code/{code}", status_code=status.HTTP_200_OK, response_model=MeetingJoinInfoResponse)
async def get_meeting_by_code_endpoint(
    code: str,
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    return await ctrl.get_meeting_by_code(code)

@router.get("/{meeting_id}", status_code=status.HTTP_200_OK, response_model=MeetingResponse)
async def get_meeting_endpoint(
    meeting_id: UUID,
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    return await ctrl.get_meeting(meeting_id)

@router.patch("/{meeting_id}", status_code=status.HTTP_200_OK, response_model=MeetingResponse)
async def update_meeting_endpoint(
    meeting_id: UUID,
    payload: MeetingUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    return await ctrl.update_meeting(current_user_id, meeting_id, payload)

@router.post("/{meeting_id}/end", status_code=status.HTTP_200_OK, response_model=MeetingResponse)
async def end_meeting_endpoint(
    meeting_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    result = await ctrl.end_meeting(current_user_id, meeting_id)
    room_id = str(meeting_id)
    await ws_connection_manager.broadcast_to_room(room_id, {
        "event": WSEvent.MEETING_ENDED,
        "data": {"meeting_id": str(meeting_id)}
    })
    return result

@router.post("/{meeting_id}/cancel", status_code=status.HTTP_200_OK, response_model=MeetingResponse)
async def cancel_meeting_endpoint(
    meeting_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    result = await ctrl.cancel_meeting(current_user_id, meeting_id)
    room_id = str(meeting_id)
    await ws_connection_manager.broadcast_to_room(room_id, {
        "event": WSEvent.MEETING_ENDED,
        "data": {"meeting_id": str(meeting_id), "cancelled": True}
    })
    return result

@router.delete("/{meeting_id}", status_code=status.HTTP_200_OK, response_model=MeetingResponse)
async def delete_meeting_endpoint(
    meeting_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    return await ctrl.delete_meeting(current_user_id, meeting_id)

@router.post("/{meeting_id}/copy-link", status_code=status.HTTP_200_OK)
async def copy_meeting_link_endpoint(
    meeting_id: UUID,
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    meeting = await ctrl.get_meeting(meeting_id)
    return {"meeting_link": meeting.meeting_link, "meeting_code": meeting.meeting_code}

@router.post("/{meeting_id}/join", status_code=status.HTTP_200_OK, response_model=MeetingJoinResponse)
async def join_meeting_endpoint(
    meeting_id: UUID,
    payload: MeetingJoinPayload,
    user_id: str = Depends(get_optional_user_id),
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    return await ctrl.join_meeting(meeting_id, user_id, payload)

@router.get("/{meeting_id}/participants", status_code=status.HTTP_200_OK, response_model=List[MeetingParticipantResponse])
async def get_participants_endpoint(
    meeting_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    return await ctrl.get_participants(meeting_id, current_user_id)

@router.post("/{meeting_id}/recordings", status_code=status.HTTP_201_CREATED, response_model=RecordingResponse)
async def upload_meeting_recording_endpoint(
    meeting_id: UUID,
    file: UploadFile = File(...),
    duration: Optional[float] = Form(None),
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    return await ctrl.upload_recording(meeting_id, current_user_id, file, duration)

@router.get("/{meeting_id}/recordings", status_code=status.HTTP_200_OK, response_model=List[RecordingResponse])
async def list_meeting_recordings_endpoint(
    meeting_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    return await ctrl.get_all_recordings(meeting_id, current_user_id)

@router.get("/recordings/{recording_id}/download", response_class=FileResponse)
async def download_recording_endpoint(
    recording_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    return await ctrl.download_recording_file(recording_id, current_user_id)

@router.delete("/recordings/{recording_id}", status_code=status.HTTP_200_OK)
async def delete_recording_endpoint(
    recording_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    return await ctrl.delete_recording(recording_id, current_user_id)


# --- TRANSCRIPTS HANDLING ---

@router.post("/{meeting_id}/transcripts", status_code=status.HTTP_201_CREATED, response_model=TranscriptResponse)
async def upload_meeting_transcript_endpoint(
    meeting_id: UUID,
    file: UploadFile = File(...),
    content_type: str = Form("text/plain"),
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    return await ctrl.upload_transcript(meeting_id, current_user_id, file, content_type)

@router.get("/{meeting_id}/transcripts", status_code=status.HTTP_200_OK, response_model=List[TranscriptResponse])
async def list_meeting_transcripts_endpoint(
    meeting_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    return await ctrl.get_all_transcripts(meeting_id, current_user_id)

@router.get("/transcripts/{transcript_id}/download", response_class=FileResponse)
async def download_transcript_endpoint(
    transcript_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    return await ctrl.download_transcript_file(transcript_id, current_user_id)

@router.delete("/transcripts/{transcript_id}", status_code=status.HTTP_200_OK)
async def delete_transcript_endpoint(
    transcript_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    return await ctrl.delete_transcript(transcript_id, current_user_id)

@router.post("/{meeting_id}/participants/{participant_id}/admit", status_code=status.HTTP_200_OK)
async def admit_participant_endpoint(
    meeting_id: UUID, participant_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    participant = await service.update_participant_status(current_user_id, meeting_id, participant_id, ParticipantStatus.ADMITTED)
    room_id = str(meeting_id)
    await ws_connection_manager.broadcast_to_room(room_id, {
        "event": WSEvent.PARTICIPANT_ADMITTED,
        "data": {
            "participant_id": str(participant.id),
            "connection_id": str(participant.id),
            "user_id": str(participant.user_id) if participant.user_id else None,
            "guest_name": participant.guest_name,
        }
    })
    return {"status": "admitted"}

@router.post("/{meeting_id}/participants/{participant_id}/reject", status_code=status.HTTP_200_OK)
async def reject_participant_endpoint(
    meeting_id: UUID, participant_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    participant = await service.update_participant_status(current_user_id, meeting_id, participant_id, ParticipantStatus.REJECTED)
    room_id = str(meeting_id)
    # Notify the rejected participant directly if connected via WebSocket (connection_id = participant.id)
    conn_id = str(participant.id)
    room_connections = ws_connection_manager.active_rooms.get(room_id, {})
    target_ws = room_connections.get(conn_id)
    if target_ws:
        await ws_connection_manager.send_personal_message({
            "event": WSEvent.PARTICIPANT_REJECTED,
            "message": "You have been rejected from the meeting."
        }, target_ws)
    return {"status": "rejected"}

@router.post("/{meeting_id}/participants/{participant_id}/remove", status_code=status.HTTP_200_OK)
async def remove_participant_endpoint(
    meeting_id: UUID, participant_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    participant = await service.update_participant_status(current_user_id, meeting_id, participant_id, ParticipantStatus.REMOVED)
    room_id = str(meeting_id)
    # Notify the removed participant directly if connected via WebSocket (connection_id = participant.id)
    conn_id = str(participant.id)
    room_connections = ws_connection_manager.active_rooms.get(room_id, {})
    target_ws = room_connections.get(conn_id)
    if target_ws:
        await ws_connection_manager.send_personal_message({
            "event": WSEvent.PARTICIPANT_REMOVED,
            "message": "You have been removed from the meeting."
        }, target_ws)
    await ws_connection_manager.broadcast_to_room(room_id, {
        "event": WSEvent.PARTICIPANT_LEFT,
        "data": {
            "connection_id": conn_id,
            "user_id": str(participant.user_id) if participant.user_id else None
        }
    })
    return {"status": "removed"}

@router.post("/{meeting_id}/participants/{participant_id}/mute", status_code=status.HTTP_200_OK)
async def mute_participant_endpoint(
    meeting_id: UUID, participant_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    participant = await service.toggle_participant_mute(current_user_id, meeting_id, participant_id, mute=True)
    room_id = str(meeting_id)
    await ws_connection_manager.broadcast_to_room(room_id, {
        "event": WSEvent.MUTE_CHANGED,
        "data": {
            "participant_id": str(participant.id),
            "is_muted": True,
        }
    })
    return {"status": "muted"}

@router.post("/{meeting_id}/participants/{participant_id}/unmute", status_code=status.HTTP_200_OK)
async def unmute_participant_endpoint(
    meeting_id: UUID, participant_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    participant = await service.toggle_participant_mute(current_user_id, meeting_id, participant_id, mute=False)
    room_id = str(meeting_id)
    await ws_connection_manager.broadcast_to_room(room_id, {
        "event": WSEvent.MUTE_CHANGED,
        "data": {
            "participant_id": str(participant.id),
            "is_muted": False,
        }
    })
    return {"status": "unmuted"}


class LeaveMeetingPayload(BaseModel):
    guest_name: Optional[str] = None
    guest_email: Optional[str] = None

@router.post("/{meeting_id}/leave", status_code=status.HTTP_200_OK, response_model=MeetingParticipantResponse)
async def leave_meeting_endpoint(
    meeting_id: UUID,
    payload: LeaveMeetingPayload = Body(default=None),
    user_id: Optional[UUID] = Depends(get_optional_user_id),
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    if user_id:
        return await ctrl.leave_meeting(meeting_id, user_id=user_id)
    if payload and payload.guest_email:
        return await ctrl.leave_meeting(meeting_id, user_id=None, guest_email=payload.guest_email)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication or guest email required to leave.")


@router.get("/{meeting_id}/waiting-count", status_code=status.HTTP_200_OK, response_model=WaitingCountResponse)
async def waiting_count_endpoint(
    meeting_id: UUID,
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    return await ctrl.get_waiting_count(meeting_id)


# --- SCREEN SHARE ---

@router.post("/{meeting_id}/screen-share/approve/{participant_id}", status_code=status.HTTP_200_OK)
async def approve_screen_share_endpoint(
    meeting_id: UUID, participant_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    participant = await service.approve_screen_share(meeting_id, current_user_id, participant_id)
    room_id = str(meeting_id)
    await ws_connection_manager.broadcast_to_room(room_id, {
        "event": WSEvent.SCREEN_SHARE_PERMISSION_GRANTED,
        "data": {
            "participant_id": str(participant.id),
            "connection_id": str(participant.id),
            "user_id": str(participant.user_id) if participant.user_id else None,
            "guest_name": participant.guest_name,
        }
    })
    return {"status": "approved"}

@router.post("/{meeting_id}/screen-share/reject/{participant_id}", status_code=status.HTTP_200_OK)
async def reject_screen_share_endpoint(
    meeting_id: UUID, participant_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    participant = await service.reject_screen_share(meeting_id, current_user_id, participant_id)
    room_id = str(meeting_id)
    conn_id = str(participant.id)
    room_connections = ws_connection_manager.active_rooms.get(room_id, {})
    target_ws = room_connections.get(conn_id)
    if target_ws:
        await ws_connection_manager.send_personal_message({
            "event": WSEvent.SCREEN_SHARE_PERMISSION_DENIED,
            "message": "Screen share request denied."
        }, target_ws)
    return {"status": "rejected"}

@router.post("/{meeting_id}/screen-share/stop", status_code=status.HTTP_200_OK)
async def force_stop_screen_share_endpoint(
    meeting_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    meeting = await service.force_stop_screen_share(meeting_id, current_user_id)
    room_id = str(meeting_id)
    await ws_connection_manager.broadcast_to_room(room_id, {
        "event": WSEvent.HOST_STOPPED_SCREEN_SHARE,
        "data": {
            "meeting_id": str(meeting_id),
        }
    })
    return {"status": "stopped"}


class ScreenShareRequestPayload(BaseModel):
    participant_id: UUID


@router.post("/{meeting_id}/screen-share/request", status_code=status.HTTP_200_OK)
async def request_screen_share_endpoint(
    meeting_id: UUID,
    payload: ScreenShareRequestPayload,
    service = Depends(get_meetings_service)
):
    try:
        participant = await service.request_screen_share(meeting_id, payload.participant_id)
    except MeetingNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except MeetingValidationError as e:
        detail = str(e)
        if "already" in detail.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    room_id = str(meeting_id)
    await ws_connection_manager.broadcast_to_room(room_id, {
        "event": WSEvent.SCREEN_SHARE_REQUESTED,
        "data": {
            "participant_id": str(participant.id),
            "connection_id": str(participant.id),
            "guest_name": participant.guest_name,
            "user_id": str(participant.user_id) if participant.user_id else None,
        }
    })
    return {"status": "requested"}

@router.post("/scheduled", status_code=status.HTTP_201_CREATED, response_model=MeetingResponse)
async def create_scheduled_meeting_endpoint(
    payload: ScheduledMeetingCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    return await ctrl.create_scheduled(current_user_id, payload)

@router.post("/{meeting_id}/invitations", status_code=status.HTTP_200_OK, response_model=List[InvitationResponse])
async def invite_participants_endpoint(
    meeting_id: UUID,
    payload: List[InvitationCreate],
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    return await ctrl.invite_participants(current_user_id, meeting_id, payload)

@router.get("/{meeting_id}/invitations", status_code=status.HTTP_200_OK, response_model=List[InvitationResponse])
async def list_invitations_endpoint(
    meeting_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    return await ctrl.list_invites(meeting_id, current_user_id)


async def get_ai_analysis_service(db: AsyncSession = Depends(get_db)) -> MeetingAIAnalysisService:
    repo = MeetingAIAnalysisRepository(db)
    provider = AIProviderService()
    # AI analysis service handles analysis only; completion emails are dispatched
    # by MeetingCompletionService via the Celery completion pipeline.
    return MeetingAIAnalysisService(repo, provider)

@meeting_analysis_router.get("", status_code=status.HTTP_200_OK, response_model=AIAnalysisResponse)
async def get_meeting_analysis_endpoint(
    meeting_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: MeetingAIAnalysisService = Depends(get_ai_analysis_service),
    meetings_service = Depends(get_meetings_service)
):
    ctrl = MeetingAIAnalysisController(service)
    session = await meetings_service.session_service.get_active_session(meeting_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active session found for this meeting.")
    try:
        await meetings_service.auth_service.verify_session_access(session.id, current_user_id, meeting_id)
    except SessionAccessDeniedException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return await ctrl.get_completed_analysis(session.id)

@meeting_analysis_router.get("/status", status_code=status.HTTP_200_OK, response_model=AIAnalysisStatusResponse)
async def get_meeting_analysis_status_endpoint(
    meeting_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: MeetingAIAnalysisService = Depends(get_ai_analysis_service),
    meetings_service = Depends(get_meetings_service)
):
    ctrl = MeetingAIAnalysisController(service)
    session = await meetings_service.session_service.get_active_session(meeting_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active session found for this meeting.")
    try:
        await meetings_service.auth_service.verify_session_access(session.id, current_user_id, meeting_id)
    except SessionAccessDeniedException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return await ctrl.get_tracking_status(session.id)


# ---------------------------------------------------------------------------
# Session History Routes (Phase 5) — registered users only, never guests
# ---------------------------------------------------------------------------

@router.get(
    "/{meeting_id}/sessions",
    status_code=status.HTTP_200_OK,
    response_model=List[SessionHistoryItemResponse],
    summary="List session history for a meeting",
)
async def list_meeting_sessions_endpoint(
    meeting_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service),
):
    ctrl = SessionHistoryController(service)
    return await ctrl.list_sessions(meeting_id, current_user_id)


@router.get(
    "/{meeting_id}/sessions/{session_id}",
    status_code=status.HTTP_200_OK,
    response_model=SessionDetailResponse,
    summary="Get a single session's details and artifact flags",
)
async def get_meeting_session_detail_endpoint(
    meeting_id: UUID,
    session_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service),
):
    ctrl = SessionHistoryController(service)
    return await ctrl.get_session_detail(meeting_id, session_id, current_user_id)


@router.get(
    "/{meeting_id}/sessions/{session_id}/recordings",
    status_code=status.HTTP_200_OK,
    response_model=List[RecordingResponse],
    summary="List recordings for a specific session (lazy-loaded)",
)
async def list_session_recordings_endpoint(
    meeting_id: UUID,
    session_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service),
):
    try:
        meeting = await service.get_meeting(meeting_id)
    except MeetingNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    try:
        await service.auth_service.verify_session_access(session_id, current_user_id, meeting_id)
    except SessionAccessDeniedException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    recordings = await service.repo.list_recordings_by_session(session_id)
    from app.modules.meetings.schemas import RecordingResponse as _RR
    return [_RR.model_validate(r) for r in recordings]


@router.get(
    "/{meeting_id}/sessions/{session_id}/transcripts",
    status_code=status.HTTP_200_OK,
    response_model=List[TranscriptResponse],
    summary="List transcripts for a specific session (lazy-loaded)",
)
async def list_session_transcripts_endpoint(
    meeting_id: UUID,
    session_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service),
):
    try:
        await service.get_meeting(meeting_id)
    except MeetingNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    try:
        await service.auth_service.verify_session_access(session_id, current_user_id, meeting_id)
    except SessionAccessDeniedException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    transcripts = await service.repo.list_transcripts_by_session(session_id)
    from app.modules.meetings.schemas import TranscriptResponse as _TR
    return [_TR.model_validate(t) for t in transcripts]


@router.get(
    "/{meeting_id}/sessions/{session_id}/analysis",
    status_code=status.HTTP_200_OK,
    response_model=AIAnalysisResponse,
    summary="Get AI analysis for a specific session (lazy-loaded)",
)
async def get_session_analysis_endpoint(
    meeting_id: UUID,
    session_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service),
    ai_service: MeetingAIAnalysisService = Depends(get_ai_analysis_service),
):
    try:
        await service.get_meeting(meeting_id)
    except MeetingNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    try:
        await service.auth_service.verify_session_access(session_id, current_user_id, meeting_id)
    except SessionAccessDeniedException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    ctrl = MeetingAIAnalysisController(ai_service)
    return await ctrl.get_completed_analysis(session_id)


@router.get(
    "/{meeting_id}/sessions/{session_id}/analysis/status",
    status_code=status.HTTP_200_OK,
    response_model=AIAnalysisStatusResponse,
    summary="Get AI analysis status for a specific session (lazy-loaded)",
)
async def get_session_analysis_status_endpoint(
    meeting_id: UUID,
    session_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service),
    ai_service: MeetingAIAnalysisService = Depends(get_ai_analysis_service),
):
    try:
        await service.get_meeting(meeting_id)
    except MeetingNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    try:
        await service.auth_service.verify_session_access(session_id, current_user_id, meeting_id)
    except SessionAccessDeniedException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    ctrl = MeetingAIAnalysisController(ai_service)
    return await ctrl.get_tracking_status(session_id)


# ---------------------------------------------------------------------------
# Session Attachment Routes — registered users only, scoped per session
# ---------------------------------------------------------------------------

async def _verify_session_access(
    meeting_id: UUID,
    session_id: UUID,
    current_user_id: UUID,
    meetings_service,
) -> None:
    """
    Reuses the existing SessionAuthorizationService.
    Raises 404 if meeting/session not found, 403 if access is denied.
    Guests (user_id=None) are always denied — this layer requires a registered user.
    """
    try:
        await meetings_service.get_meeting(meeting_id)
    except MeetingNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    try:
        await meetings_service.auth_service.verify_session_access(
            session_id, current_user_id, meeting_id
        )
    except SessionAccessDeniedException as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.post(
    "/{meeting_id}/sessions/{session_id}/attachments",
    status_code=status.HTTP_201_CREATED,
    response_model=AttachmentResponse,
    summary="Upload an attachment to a meeting session",
)
async def upload_session_attachment(
    meeting_id: UUID,
    session_id: UUID,
    file: UploadFile = File(...),
    current_user_id: UUID = Depends(get_current_user_id),
    meetings_service = Depends(get_meetings_service),
    attachment_service: AttachmentService = Depends(get_attachment_service),
):
    await _verify_session_access(meeting_id, session_id, current_user_id, meetings_service)
    try:
        attachment = await attachment_service.upload(
            owner_user_id=current_user_id,
            entity_type=AttachmentEntityType.MEETING_SESSION,
            entity_id=session_id,
            file=file,
        )
        return AttachmentResponse.model_validate(attachment)
    except AttachmentValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except AttachmentStorageError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get(
    "/{meeting_id}/sessions/{session_id}/attachments",
    status_code=status.HTTP_200_OK,
    response_model=AttachmentListResponse,
    summary="List all attachments for a meeting session",
)
async def list_session_attachments(
    meeting_id: UUID,
    session_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    meetings_service = Depends(get_meetings_service),
    attachment_service: AttachmentService = Depends(get_attachment_service),
):
    await _verify_session_access(meeting_id, session_id, current_user_id, meetings_service)
    attachments = await attachment_service.list_all_for_entity(
        AttachmentEntityType.MEETING_SESSION, session_id
    )
    return AttachmentListResponse(
        attachments=[AttachmentResponse.model_validate(a) for a in attachments],
        total_count=len(attachments),
    )


@router.get(
    "/{meeting_id}/sessions/{session_id}/attachments/{attachment_id}/download",
    response_class=FileResponse,
    summary="Download a meeting session attachment",
)
async def download_session_attachment(
    meeting_id: UUID,
    session_id: UUID,
    attachment_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    meetings_service = Depends(get_meetings_service),
    attachment_service: AttachmentService = Depends(get_attachment_service),
):
    await _verify_session_access(meeting_id, session_id, current_user_id, meetings_service)
    try:
        attachment = await attachment_service.get_for_download_verified(
            attachment_id, AttachmentEntityType.MEETING_SESSION, session_id
        )
        return FileResponse(
            path=attachment.storage_path,
            media_type=attachment.content_type,
            filename=attachment.original_filename,
        )
    except AttachmentNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")


@router.delete(
    "/{meeting_id}/sessions/{session_id}/attachments/{attachment_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a meeting session attachment",
)
async def delete_session_attachment(
    meeting_id: UUID,
    session_id: UUID,
    attachment_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    meetings_service = Depends(get_meetings_service),
    attachment_service: AttachmentService = Depends(get_attachment_service),
):
    await _verify_session_access(meeting_id, session_id, current_user_id, meetings_service)
    try:
        await attachment_service.delete_verified(
            attachment_id, AttachmentEntityType.MEETING_SESSION, session_id
        )
        return {"status": "success", "message": "Attachment deleted successfully."}
    except AttachmentNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")


@router.get("/recent-analyses", status_code=status.HTTP_200_OK, response_model=List[RecentAIAnalysisItem])
async def list_recent_analyses_endpoint(
    limit: int = Query(5, ge=1, le=20),
    current_user_id: UUID = Depends(get_current_user_id),
    ai_service: MeetingAIAnalysisService = Depends(get_ai_analysis_service),
):
    ctrl = MeetingAIAnalysisController(ai_service)
    return await ctrl.list_recent_analyses(current_user_id, limit)
