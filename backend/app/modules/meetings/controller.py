from typing import Optional, List
from uuid import UUID
from fastapi import HTTPException, status, UploadFile
from fastapi.responses import FileResponse

from app.modules.meetings.service import MeetingService, MeetingAIAnalysisService
from app.modules.meetings.schemas import (
    MeetingCreate, MeetingUpdate, MeetingResponse,
    MeetingParticipantResponse, MeetingJoinPayload,
    MeetingJoinInfoResponse, MeetingJoinResponse, TranscriptResponse, RecordingResponse,
    WaitingCountResponse, ScheduledMeetingCreate, ScheduledMeetingUpdate, InvitationCreate, InvitationResponse, AIAnalysisResponse, AIAnalysisStatusResponse, AIAnalysisPayloadSchema
)
from app.modules.meetings.exceptions import (
    MeetingNotFoundException, MeetingAccessDeniedException, MeetingValidationError
)

class MeetingController:
    def __init__(self, service: MeetingService):
        self.service = service

    async def create_meeting(self, host_id: UUID, payload: MeetingCreate) -> dict:
        meeting = await self.service.create_meeting(host_id, payload)
        return MeetingResponse.model_validate(meeting)

    async def get_meeting(self, meeting_id: UUID) -> dict:
        try:
            meeting = await self.service.get_meeting(meeting_id)
            return MeetingResponse.model_validate(meeting)
        except MeetingNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    async def update_meeting(self, user_id: UUID, meeting_id: UUID, payload: MeetingUpdate) -> dict:
        try:
            meeting = await self.service.update_meeting(user_id, meeting_id, payload)
            return MeetingResponse.model_validate(meeting)
        except MeetingNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except MeetingAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except MeetingValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def list_user_meetings(self, user_id: UUID) -> List[dict]:
        meetings = await self.service.list_meetings(user_id)
        return [MeetingResponse.model_validate(m) for m in meetings]

    async def end_meeting(self, user_id: UUID, meeting_id: UUID) -> dict:
        try:
            meeting = await self.service.end_meeting(user_id, meeting_id)
            return MeetingResponse.model_validate(meeting)
        except MeetingNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except MeetingAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except MeetingValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def cancel_meeting(self, user_id: UUID, meeting_id: UUID) -> dict:
        try:
            meeting = await self.service.cancel_meeting(user_id, meeting_id)
            return MeetingResponse.model_validate(meeting)
        except MeetingNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except MeetingAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except MeetingValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def join_meeting(self, meeting_id: UUID, user_id: Optional[UUID], payload: MeetingJoinPayload) -> MeetingJoinResponse:
        try:
            participant = await self.service.join_meeting_flow(
                meeting_id=meeting_id, user_id=user_id, guest_name=payload.guest_name, guest_email=payload.guest_email
            )
            session_token = MeetingService.generate_meeting_session_token(participant.id, meeting_id)
            return MeetingJoinResponse(
                id=participant.id,
                meeting_id=participant.meeting_id,
                user_id=participant.user_id,
                guest_name=participant.guest_name,
                guest_email=participant.guest_email,
                participant_type=participant.participant_type,
                status=participant.status,
                is_muted=participant.is_muted,
                can_start_screen_share=participant.can_start_screen_share,
                joined_at=participant.joined_at,
                left_at=participant.left_at,
                meeting_session_token=session_token,
            )
        except MeetingNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except MeetingValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_meeting_by_code(self, code: str) -> dict:
        try:
            meeting, host_name = await self.service.get_meeting_by_code(code)
            response = MeetingJoinInfoResponse.model_validate(meeting, from_attributes=True)
            return {**response.model_dump(), "host_name": host_name}
        except MeetingNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    async def get_participants(self, meeting_id: UUID) -> List[dict]:
        try:
            participants = await self.service.list_participants(meeting_id)
            return [MeetingParticipantResponse.model_validate(p) for p in participants]
        except MeetingNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    async def leave_meeting(self, meeting_id: UUID, user_id: Optional[UUID], guest_email: Optional[str] = None) -> dict:
        try:
            participant = await self.service.leave_meeting(meeting_id, user_id=user_id, guest_email=guest_email)
            return MeetingParticipantResponse.model_validate(participant)
        except MeetingValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_waiting_count(self, meeting_id: UUID) -> dict:
        try:
            count = await self.service.get_waiting_count(meeting_id)
            return WaitingCountResponse(waiting_count=count)
        except MeetingNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    async def upload_recording(self, meeting_id: UUID, file: UploadFile, duration: Optional[float]) -> dict:
        try:
            artifact = await self.service.save_recording_file(meeting_id, file, duration)
            return RecordingResponse.model_validate(artifact)
        except MeetingNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    async def upload_transcript(self, meeting_id: UUID, file: UploadFile, content_type: str = "text/plain") -> dict:
        try:
            artifact = await self.service.save_transcript_file(meeting_id, file, content_type)
            return TranscriptResponse.model_validate(artifact)
        except MeetingNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    async def get_all_recordings(self, meeting_id: UUID) -> List[dict]:
        recordings = await self.service.list_recordings(meeting_id)
        return [RecordingResponse.model_validate(r) for r in recordings]

    async def get_all_transcripts(self, meeting_id: UUID) -> List[dict]:
        transcripts = await self.service.list_transcripts(meeting_id)
        return [TranscriptResponse.model_validate(t) for t in transcripts]

    async def download_recording_file(self, rec_id: UUID) -> FileResponse:
        try:
            artifact = await self.service.get_recording_artifact(rec_id)
            return FileResponse(
                path=artifact.storage_path,
                media_type=artifact.content_type,
                filename=artifact.filename
            )
        except MeetingNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    async def download_transcript_file(self, tx_id: UUID) -> FileResponse:
        try:
            artifact = await self.service.get_transcript_artifact(tx_id)
            return FileResponse(
                path=artifact.storage_path,
                media_type="text/plain",
                filename=artifact.filename
            )
        except MeetingNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    async def delete_meeting(self, user_id: UUID, meeting_id: UUID) -> dict:
        try:
            meeting = await self.service.delete_meeting(user_id, meeting_id)
            return MeetingResponse.model_validate(meeting)
        except MeetingNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except MeetingAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def create_scheduled(self, host_id: UUID, payload: ScheduledMeetingCreate) -> dict:
        meeting = await self.service.create_scheduled_meeting(host_id, payload)
        return MeetingResponse.model_validate(meeting)

    async def invite_participants(self, user_id: UUID, meeting_id: UUID, invites: List[InvitationCreate]) -> List[dict]:
        invitations = await self.service.add_invitations(user_id, meeting_id, invites)
        return [InvitationResponse.model_validate(i) for i in invitations]

    async def list_invites(self, meeting_id: UUID) -> List[dict]:
        invitations = await self.service.repo.list_invitations(meeting_id)
        return [InvitationResponse.model_validate(i) for i in invitations]

    async def delete_recording(self, rec_id: UUID) -> dict:
        await self.service.remove_recording(rec_id)
        return {"status": "success", "message": "Recording artifact removed completely."}

    async def delete_transcript(self, tx_id: UUID) -> dict:
        await self.service.remove_transcript(tx_id)
        return {"status": "success", "message": "Transcript artifact removed completely."}

class MeetingAIAnalysisController:
    def __init__(self, service: MeetingAIAnalysisService):
        self.service = service

    async def get_completed_analysis(self, meeting_id: UUID) -> dict:
        analysis = await self.service.get_analysis(meeting_id)
        return AIAnalysisResponse.model_validate(analysis)

    async def get_tracking_status(self, meeting_id: UUID) -> dict:
        analysis = await self.service.get_analysis_status(meeting_id)
        return AIAnalysisStatusResponse.model_validate(analysis)
