from __future__ import annotations
from datetime import datetime, timezone, timedelta
import jwt
from typing import Optional, Sequence, List
from uuid import UUID

from fastapi import HTTPException, status

from app.core.storage import StorageService
from app.modules.meetings.repository import MeetingRepository, MeetingAIAnalysisRepository, MeetingSessionRepository
from app.modules.meetings.ai_provider_service import AIProviderService
from app.models.meetings import Meeting, MeetingParticipant, MeetingRecording, MeetingTranscript, MeetingInvitation, MeetingSession, AIAnalysisStatus, MeetingAIAnalysis
from app.modules.meetings.schemas import MeetingCreate, MeetingUpdate, ScheduledMeetingCreate, ScheduledMeetingUpdate, InvitationCreate, InvitationResponse
from app.modules.meetings.enums import MeetingStatus, MeetingType, ParticipantType, ParticipantStatus, SessionStatus, AIAnalysisStatus
from app.modules.meetings.exceptions import (
    MeetingNotFoundException,
    MeetingAccessDeniedException,
    SessionAccessDeniedException,
    MeetingValidationError
)
from app.core.config import settings
from app.core.logger import logger
from app.workers.tasks import send_async_email
from redis.asyncio import Redis

class MeetingService:
    def __init__(self, repo: MeetingRepository, storage: StorageService, session_service: MeetingSessionService, auth_service=None):
        self.repo = repo
        self.storage = storage
        self.session_service = session_service
        self.auth_service = auth_service

    async def create_meeting(self, host_id: UUID, payload: MeetingCreate) -> Meeting:
        return await self.repo.create(host_id, payload.model_dump())

    async def get_meeting(self, meeting_id: UUID) -> Meeting:
        meeting = await self.repo.get_by_id(meeting_id)
        if not meeting:
            raise MeetingNotFoundException(meeting_id)
        meeting.invited_participants_count = await self.repo.count_invitations(meeting_id)
        return meeting

    async def update_meeting(self, user_id: UUID, meeting_id: UUID, payload: MeetingUpdate) -> Meeting:
        meeting = await self.get_meeting(meeting_id)
        if meeting.host_id != user_id:
            raise MeetingAccessDeniedException(meeting_id, user_id)
        if meeting.status in (MeetingStatus.CANCELLED, MeetingStatus.ENDED):
            raise MeetingValidationError(f"Cannot update a meeting that has already been {meeting.status.value.lower()}.")

        return await self.repo.update(meeting, payload.model_dump(exclude_unset=True))

    async def list_meetings(self, user_id: UUID) -> Sequence[Meeting]:
        return await self.repo.list_user_meetings(user_id)

    async def _clear_screen_sharer_if_needed(self, meeting_id: UUID, participant_id: UUID) -> None:
        meeting = await self.repo.get_by_id(meeting_id)
        if meeting and meeting.active_screen_sharer_id == participant_id:
            await self.repo.update(meeting, {"active_screen_sharer_id": None})

    async def end_meeting(self, user_id: UUID, meeting_id: UUID) -> Meeting:
        meeting = await self.get_meeting(meeting_id)
        if meeting.host_id != user_id:
            raise MeetingAccessDeniedException(meeting_id, user_id)
        if meeting.status not in (MeetingStatus.ACTIVE, MeetingStatus.IDLE):
            raise MeetingValidationError("Only active or idle meetings can be ended.")

        now = datetime.now(timezone.utc)
        participants = await self.repo.get_participants_list(meeting_id, active_only=False)
        for p in participants:
            if p.status not in (ParticipantStatus.LEFT, ParticipantStatus.REMOVED, ParticipantStatus.REJECTED):
                update = {"status": ParticipantStatus.LEFT, "left_at": now}
                if meeting.active_screen_sharer_id == p.id:
                    update["can_start_screen_share"] = False
                await self.repo.update_participant(p, update)

        active_session = await self.session_service.get_active_session(meeting_id)
        if active_session:
            await self.session_service.finish_session(active_session.id)

        new_status = MeetingStatus.ENDED if meeting.meeting_type == MeetingType.SCHEDULED else MeetingStatus.IDLE
        result = await self.repo.update(meeting, {"status": new_status, "ended_at": now, "active_screen_sharer_id": None})

        if active_session:
            await self._trigger_completion_pipeline(active_session.id)

        return result

    async def _trigger_completion_pipeline(self, session_id: UUID) -> None:
        from app.workers.tasks import analyze_meeting_transcript

        try:
            analyze_meeting_transcript.delay(str(session_id))
        except Exception as e:
            logger.error(f"Failed to queue completion pipeline for meeting session {session_id}: {e}")

    async def cancel_meeting(self, user_id: UUID, meeting_id: UUID) -> Meeting:
        meeting = await self.get_meeting(meeting_id)
        if meeting.host_id != user_id:
            raise MeetingAccessDeniedException(meeting_id, user_id)
        if meeting.status == MeetingStatus.CANCELLED:
            raise MeetingValidationError("Meeting has already been cancelled.")
        if meeting.status == MeetingStatus.ENDED:
            raise MeetingValidationError("Cannot cancel a meeting that has already ended.")

        active_session = await self.session_service.get_active_session(meeting_id)
        if active_session:
            await self.session_service.finish_session(active_session.id)

        return await self.repo.update(meeting, {"status": MeetingStatus.CANCELLED, "ended_at": datetime.now(timezone.utc), "active_screen_sharer_id": None})

    async def delete_meeting(self, user_id: UUID, meeting_id: UUID) -> Meeting:
        meeting = await self.get_meeting(meeting_id)
        if meeting.host_id != user_id:
            raise MeetingAccessDeniedException(meeting_id, user_id)
        await self.session_service.remove_live_state(meeting_id)
        await self.repo.soft_delete(meeting)
        return meeting

    async def get_meeting_by_code(self, code: str) -> tuple:
        meeting = await self.repo.get_by_code(code, include_deleted=True)
        if not meeting:
            raise MeetingNotFoundException(f"Meeting with code '{code}' not found or has been removed.")
        if meeting.deleted_at:
            raise MeetingNotFoundException("This meeting no longer exists.")
        host_name = await self.repo.get_user_name_by_id(meeting.host_id) or "Unknown"
        meeting.invited_participants_count = await self.repo.count_invitations(meeting.id)
        return meeting, host_name

    async def leave_meeting_flow(self, meeting_id: UUID, user_id: Optional[UUID] = None, guest_email: Optional[str] = None) -> None:
        session = await self.session_service.get_active_session(meeting_id)
        if not session:
            return
        participant = await self.repo.get_active_participant(session.id, user_id=user_id, guest_email=guest_email)
        if participant:
            await self._clear_screen_sharer_if_needed(meeting_id, participant.id)
            await self.repo.update_participant(participant, {
                "status": ParticipantStatus.LEFT,
                "left_at": datetime.now(timezone.utc)
            })
            await self._transition_to_idle_if_empty(meeting_id)

    async def list_participants(self, meeting_id: UUID, user_id: Optional[UUID] = None) -> Sequence[MeetingParticipant]:
        meeting = await self.get_meeting(meeting_id)
        is_host = (user_id is not None and meeting.host_id == user_id)
        if is_host:
            return await self.repo.get_participants_by_meeting(meeting_id)
        if user_id is not None:
            accessible_ids = await self.auth_service.get_accessible_session_ids(user_id, meeting_id)
            if not accessible_ids:
                return []
            return await self.repo.get_participants_by_session_ids(accessible_ids)
        return []

    async def save_recording_file(self, meeting_id: UUID, user_id: UUID, file, duration: Optional[float] = None) -> MeetingRecording:
        meeting = await self.get_meeting(meeting_id)
        active_session = await self.session_service.get_active_session(meeting_id)
        if not active_session:
            raise MeetingValidationError("No active session for this meeting.")

        await self.auth_service.verify_session_access(active_session.id, user_id, meeting_id)

        content = await file.read()
        content_type = file.content_type or "audio/webm"
        result = await self.storage.save_recording(
            session_id=active_session.id,
            filename=file.filename or "recording.webm",
            content=content,
            content_type=content_type,
        )

        recording_data = {
            "session_id": active_session.id,
            "filename": result["filename"],
            "content_type": content_type,
            "size": result["size"],
            "duration": duration,
            "storage_path": result["storage_path"],
        }
        return await self.repo.add_recording(recording_data)

    async def save_transcript_file(self, meeting_id: UUID, user_id: UUID, file, content_type: str = "text/plain") -> MeetingTranscript:
        meeting = await self.get_meeting(meeting_id)
        active_session = await self.session_service.get_active_session(meeting_id)
        if not active_session:
            raise MeetingValidationError("No active session for this meeting.")

        await self.auth_service.verify_session_access(active_session.id, user_id, meeting_id)

        content = await file.read()
        result = await self.storage.save_transcript(
            session_id=active_session.id,
            filename=file.filename or "transcript.txt",
            content=content,
            content_type=content_type,
        )

        transcript_data = {
            "session_id": active_session.id,
            "filename": result["filename"],
            "content_type": content_type,
            "size": result["size"],
            "storage_path": result["storage_path"],
        }
        return await self.repo.add_transcript(transcript_data)

    async def get_recording_artifact(self, rec_id: UUID, user_id: Optional[UUID] = None) -> MeetingRecording:
        rec = await self.repo.get_recording_by_id(rec_id)
        if not rec or not self.storage.exists(rec.storage_path):
            raise MeetingNotFoundException(rec_id)
        session = await self.repo.get_session_by_recording_id(rec_id)
        if not session:
            raise MeetingNotFoundException(rec_id)
        meeting = await self.repo.get_by_id(session.meeting_id)
        if not meeting:
            raise MeetingNotFoundException(rec_id)
        await self.auth_service.verify_session_access(session.id, user_id, meeting.id)
        return rec

    async def get_transcript_artifact(self, tx_id: UUID, user_id: Optional[UUID] = None) -> MeetingTranscript:
        tx = await self.repo.get_transcript_by_id(tx_id)
        if not tx or not self.storage.exists(tx.storage_path):
            raise MeetingNotFoundException(tx_id)
        session = await self.repo.get_session_by_transcript_id(tx_id)
        if not session:
            raise MeetingNotFoundException(tx_id)
        meeting = await self.repo.get_by_id(session.meeting_id)
        if not meeting:
            raise MeetingNotFoundException(tx_id)
        await self.auth_service.verify_session_access(session.id, user_id, meeting.id)
        return tx

    async def list_recordings(self, meeting_id: UUID, user_id: Optional[UUID] = None) -> Sequence[MeetingRecording]:
        meeting = await self.get_meeting(meeting_id)
        is_host = (user_id is not None and meeting.host_id == user_id)
        if is_host:
            return await self.repo.list_recordings_by_meeting(meeting_id)
        accessible_ids = await self.auth_service.get_accessible_session_ids(user_id, meeting_id)
        if not accessible_ids:
            return []
        return await self.repo.list_recordings_by_session_ids(accessible_ids)

    async def list_transcripts(self, meeting_id: UUID, user_id: Optional[UUID] = None) -> Sequence[MeetingTranscript]:
        meeting = await self.get_meeting(meeting_id)
        is_host = (user_id is not None and meeting.host_id == user_id)
        if is_host:
            return await self.repo.list_transcripts_by_meeting(meeting_id)
        accessible_ids = await self.auth_service.get_accessible_session_ids(user_id, meeting_id)
        if not accessible_ids:
            return []
        return await self.repo.list_transcripts_by_session_ids(accessible_ids)

    async def remove_recording(self, rec_id: UUID, user_id: Optional[UUID] = None) -> None:
        rec = await self.repo.get_recording_by_id(rec_id)
        if not rec:
            return
        meeting = await self.repo.get_meeting_by_recording_id(rec_id)
        if not meeting:
            raise MeetingNotFoundException(rec_id)
        if user_id is None or meeting.host_id != user_id:
            raise MeetingAccessDeniedException(meeting.id, user_id or UUID(int=0))
        await self.storage.delete_file(rec.storage_path)
        await self.repo.delete_recording_meta(rec)

    async def remove_transcript(self, tx_id: UUID, user_id: Optional[UUID] = None) -> None:
        tx = await self.repo.get_transcript_by_id(tx_id)
        if not tx:
            return
        meeting = await self.repo.get_meeting_by_transcript_id(tx_id)
        if not meeting:
            raise MeetingNotFoundException(tx_id)
        if user_id is None or meeting.host_id != user_id:
            raise MeetingAccessDeniedException(meeting.id, user_id or UUID(int=0))
        await self.storage.delete_file(tx.storage_path)
        await self.repo.delete_transcript_meta(tx)

    async def join_meeting_flow(self, meeting_id: UUID, user_id: Optional[UUID] = None, guest_name: Optional[str] = None, guest_email: Optional[str] = None) -> MeetingParticipant:
        meeting = await self.repo.get_by_id(meeting_id, include_deleted=True)
        if not meeting:
            raise MeetingValidationError("The meeting link is invalid or the meeting has been cancelled.")
        if meeting.deleted_at:
            raise MeetingValidationError("This meeting no longer exists.")
        if meeting.status == MeetingStatus.CANCELLED:
            raise MeetingValidationError("The meeting link is invalid or the meeting has been cancelled.")

        # Only INSTANT meetings are reusable — SCHEDULED meetings cannot be rejoined
        if meeting.status in (MeetingStatus.ENDED, MeetingStatus.IDLE):
            if meeting.meeting_type == MeetingType.SCHEDULED:
                raise MeetingValidationError("This meeting has ended and cannot be rejoined.")
            await self.repo.update(meeting, {"status": MeetingStatus.ACTIVE, "ended_at": None})
            meeting.status = MeetingStatus.ACTIVE

        is_host = (user_id is not None and meeting.host_id == user_id)

        if meeting.meeting_type == MeetingType.SCHEDULED and not is_host:
            now = datetime.now(timezone.utc)
            earliest_join_time = meeting.scheduled_start - timedelta(minutes=15)

            if now < earliest_join_time:
                raise MeetingValidationError(f"This meeting is locked. You can join starting 15 minutes before scheduled start time.")
            target_email = None
            if user_id:
                user_record = await self.repo.get_user_by_id(user_id)
                target_email = user_record.email if user_record else None
            else:
                if not guest_email:
                    raise MeetingValidationError("An invited email validation parameter is required to join this session.")
                target_email = guest_email
            if not target_email or not (await self.repo.get_invitation_by_email(meeting_id, target_email)):
                raise MeetingAccessDeniedException(meeting_id, user_id or UUID(int=0))
        initial_status = ParticipantStatus.ADMITTED if is_host else ParticipantStatus.WAITING

        if is_host and meeting.status == MeetingStatus.CREATED:
            await self.repo.update(meeting, {"status": MeetingStatus.ACTIVE})
            meeting.status = MeetingStatus.ACTIVE

        # Ensure an active session exists for the meeting
        active_session = None
        if meeting.status == MeetingStatus.ACTIVE:
            active_session = await self.session_service.get_active_session(meeting.id)
            if not active_session:
                active_session = await self.session_service.create_session(meeting.id, meeting.host_id)

        initial_status = ParticipantStatus.ADMITTED if is_host else ParticipantStatus.WAITING

        if user_id:
            p_type = ParticipantType.REGISTERED
            existing = await self.repo.get_active_participant(active_session.id, user_id=user_id)
            if existing:
                if existing.status == ParticipantStatus.REMOVED:
                    raise MeetingAccessDeniedException(meeting_id, user_id)
                if is_host and not existing.can_start_screen_share:
                    await self.repo.update_participant(existing, {"can_start_screen_share": True})
                return existing
            last = await self.repo.get_last_participant(active_session.id, user_id=user_id)
            if last and last.status == ParticipantStatus.LEFT:
                now = datetime.now(timezone.utc)
                await self.repo.update_participant(last, {
                    "status": initial_status,
                    "left_at": None,
                    "joined_at": now,
                    "is_muted": False,
                    "can_start_screen_share": is_host,
                })
                return last
        else:
            if not guest_email or not guest_email.strip():
                raise MeetingValidationError("Guest email is required to join a temporary session.")
            guest_email = guest_email.strip().lower()
            p_type = ParticipantType.GUEST
            existing = await self.repo.get_active_participant(active_session.id, guest_email=guest_email)
            if existing:
                if existing.status == ParticipantStatus.REMOVED:
                    raise MeetingValidationError("You have been removed from this meeting room container.")
                if guest_name:
                    await self.repo.update_participant(existing, {"guest_name": guest_name.strip()})
                return existing
            last = await self.repo.get_last_participant(active_session.id, guest_email=guest_email)
            if last and last.status == ParticipantStatus.LEFT:
                now = datetime.now(timezone.utc)
                update_data = {
                    "status": ParticipantStatus.WAITING,
                    "left_at": None,
                    "joined_at": now,
                    "is_muted": False,
                }
                if guest_name:
                    update_data["guest_name"] = guest_name.strip()
                await self.repo.update_participant(last, update_data)
                return last

        participant = await self.repo.create_participant(
            session_id=active_session.id,
            user_id=user_id,
            guest_name=guest_name.strip() if guest_name else None,
            guest_email=guest_email,
            p_type=p_type,
            status=initial_status
        )
        if is_host:
            await self.repo.update_participant(participant, {"can_start_screen_share": True})
        return participant

    async def update_participant_status(self, executioner_id: UUID, meeting_id: UUID, participant_id: UUID, new_status: ParticipantStatus) -> MeetingParticipant:
        """Host-only action to transition participant states."""
        meeting = await self.get_meeting(meeting_id)
        if meeting.host_id != executioner_id:
            raise MeetingAccessDeniedException(meeting_id, executioner_id)

        participant = await self.repo.get_participant_by_id(participant_id)
        await self._validate_participant_in_meeting(participant, meeting_id)

        # Validate state transitions
        if new_status == ParticipantStatus.ADMITTED:
            if participant.status == ParticipantStatus.ADMITTED:
                return participant
            if participant.status != ParticipantStatus.WAITING:
                raise MeetingValidationError("Can only admit participants who are waiting.")
        elif new_status == ParticipantStatus.REJECTED:
            if participant.status != ParticipantStatus.WAITING:
                raise MeetingValidationError("Can only reject participants who are waiting.")
        elif new_status == ParticipantStatus.REMOVED:
            if participant.status != ParticipantStatus.ADMITTED:
                raise MeetingValidationError("Can only remove admitted participants.")

        update_data = {"status": new_status}
        if new_status == ParticipantStatus.REMOVED:
            await self._clear_screen_sharer_if_needed(meeting_id, participant_id)
        if new_status in [ParticipantStatus.LEFT, ParticipantStatus.REMOVED, ParticipantStatus.REJECTED]:
            update_data["left_at"] = datetime.now(timezone.utc)
        participant = await self.repo.update_participant(participant, update_data)
        return participant

    async def toggle_participant_mute(self, executioner_id: UUID, meeting_id: UUID, participant_id: UUID, mute: bool) -> MeetingParticipant:
        """Host-only action to manage standard device muting tracks."""
        meeting = await self.get_meeting(meeting_id)
        if meeting.host_id != executioner_id:
            raise MeetingAccessDeniedException(meeting_id, executioner_id)

        participant = await self.repo.get_participant_by_id(participant_id)
        await self._validate_participant_in_meeting(participant, meeting_id)

        participant = await self.repo.update_participant(participant, {"is_muted": mute})
        return participant

    async def _transition_to_idle_if_empty(self, meeting_id: UUID) -> None:
        participants = await self.repo.get_participants_by_meeting(meeting_id, active_only=True)
        if len(participants) == 0:
            meeting = await self.repo.get_by_id(meeting_id, include_deleted=True)
            if meeting and meeting.status != MeetingStatus.IDLE:
                await self.repo.update(meeting, {"status": MeetingStatus.IDLE})

    async def leave_meeting(self, meeting_id: UUID, user_id: Optional[UUID] = None, guest_email: Optional[str] = None) -> MeetingParticipant:
        session = await self.session_service.get_active_session(meeting_id)
        if not session:
            raise MeetingValidationError("No active session found for this meeting.")
        participant = await self.repo.get_active_participant(session.id, user_id=user_id, guest_email=guest_email)
        if not participant:
            last = await self.repo.get_last_participant(session.id, user_id=user_id, guest_email=guest_email)
            if last and last.status == ParticipantStatus.LEFT:
                return last
            raise MeetingValidationError("You are not an active participant in this meeting.")
        if participant.status == ParticipantStatus.WAITING:
            raise MeetingValidationError("You have not been admitted yet. Use reject to leave the waiting room.")

        await self._clear_screen_sharer_if_needed(meeting_id, participant.id)
        participant = await self.repo.update_participant(participant, {
            "status": ParticipantStatus.LEFT,
            "left_at": datetime.now(timezone.utc)
        })
        await self._transition_to_idle_if_empty(meeting_id)
        return participant

    async def get_waiting_count(self, meeting_id: UUID) -> int:
        participants = await self.repo.get_participants_by_meeting(meeting_id)
        return sum(1 for p in participants if p.status == ParticipantStatus.WAITING)

    async def request_screen_share(self, meeting_id: UUID, participant_id: UUID) -> MeetingParticipant:
        meeting = await self.get_meeting(meeting_id)
        logger.info("[screen_share_request] participant_id=%s participant.status=N/A meeting.status=%s can_start_screen_share=N/A reason=checking_meeting_active", participant_id, meeting.status.value if meeting else "NONE")
        if meeting.status != MeetingStatus.ACTIVE:
            logger.warning("[screen_share_request] REJECTED participant_id=%s meeting.status=%s reason=meeting_not_active", participant_id, meeting.status.value)
            raise MeetingValidationError("Meeting is not active.")
        participant = await self.repo.get_participant_by_id(participant_id)
        logger.info("[screen_share_request] participant_id=%s participant.status=%s meeting.status=%s can_start_screen_share=%s reason=checking_participant_exists", participant_id, participant.status.value if participant else "NOT_FOUND", meeting.status.value, participant.can_start_screen_share if participant else "N/A")
        await self._validate_participant_in_meeting(participant, meeting_id)
        if participant.status != ParticipantStatus.ADMITTED:
            logger.warning("[screen_share_request] REJECTED participant_id=%s participant.status=%s reason=not_admitted", participant_id, participant.status.value)
            raise MeetingValidationError("Participant must be admitted to request screen share.")
        if participant.can_start_screen_share:
            logger.warning("[screen_share_request] REJECTED participant_id=%s reason=already_has_permission", participant_id)
            raise MeetingValidationError("Screen share permission already granted.")
        logger.info("[screen_share_request] ACCEPTED participant_id=%s", participant_id)
        return participant

    async def approve_screen_share(self, meeting_id: UUID, host_id: UUID, participant_id: UUID) -> MeetingParticipant:
        meeting = await self.get_meeting(meeting_id)
        if meeting.host_id != host_id:
            raise MeetingAccessDeniedException(meeting_id, host_id)
        participant = await self.repo.get_participant_by_id(participant_id)
        await self._validate_participant_in_meeting(participant, meeting_id)
        participant = await self.repo.update_participant(participant, {"can_start_screen_share": True})
        return participant

    async def reject_screen_share(self, meeting_id: UUID, host_id: UUID, participant_id: UUID) -> MeetingParticipant:
        meeting = await self.get_meeting(meeting_id)
        if meeting.host_id != host_id:
            raise MeetingAccessDeniedException(meeting_id, host_id)
        participant = await self.repo.get_participant_by_id(participant_id)
        await self._validate_participant_in_meeting(participant, meeting_id)
        return participant

    async def start_screen_share(self, meeting_id: UUID, participant_id: UUID, user_id: Optional[UUID] = None, guest_name: Optional[str] = None) -> Meeting:
        meeting = await self.get_meeting(meeting_id)
        if meeting.status != MeetingStatus.ACTIVE:
            raise MeetingValidationError("Meeting is not active.")
        if meeting.active_screen_sharer_id is not None:
            raise MeetingValidationError("Another participant is already sharing their screen.")

        participant = await self.repo.get_participant_by_id(participant_id)
        await self._validate_participant_in_meeting(participant, meeting_id)

        is_host = user_id is not None and meeting.host_id == user_id
        if not is_host and not participant.can_start_screen_share:
            raise MeetingValidationError("You do not have permission to share your screen.")

        meeting = await self.repo.update(meeting, {"active_screen_sharer_id": participant_id})
        return meeting

    async def stop_screen_share(self, meeting_id: UUID, participant_id: UUID) -> Meeting:
        meeting = await self.get_meeting(meeting_id)
        if meeting.active_screen_sharer_id != participant_id:
            raise MeetingValidationError("You are not the active screen sharer.")
        meeting = await self.repo.update(meeting, {"active_screen_sharer_id": None})
        return meeting

    async def force_stop_screen_share(self, meeting_id: UUID, host_id: UUID) -> Meeting:
        meeting = await self.get_meeting(meeting_id)
        if meeting.host_id != host_id:
            raise MeetingAccessDeniedException(meeting_id, host_id)
        meeting = await self.repo.update(meeting, {"active_screen_sharer_id": None})
        return meeting

    async def _validate_participant_in_meeting(self, participant: MeetingParticipant | None, meeting_id: UUID) -> MeetingSession:
        if not participant:
            raise MeetingValidationError("Target participant not found.")
        session = await self.session_service.repo.get_by_id(participant.session_id)
        if not session or session.meeting_id != meeting_id:
            raise MeetingValidationError("Target participant node context matching failed.")
        return session

    @staticmethod
    def generate_meeting_session_token(participant_id: UUID, meeting_id: UUID) -> str:
        payload = {
            "participant_id": str(participant_id),
            "meeting_id": str(meeting_id),
        }
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.MEETING_SESSION_TOKEN_EXPIRE_MINUTES)
        payload["exp"] = int(expire.timestamp())
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

    async def create_scheduled_meeting(self, host_id: UUID, payload: ScheduledMeetingCreate) -> Meeting:
        data = payload.model_dump(exclude={"invitations"})
        data["meeting_type"] = MeetingType.SCHEDULED
        data["status"] = MeetingStatus.SCHEDULED
        data["scheduled_by"] = host_id

        meeting = await self.repo.create(host_id, data)

        formatted_date = payload.scheduled_start.strftime('%Y-%m-%d')
        formatted_time = payload.scheduled_start.strftime('%H:%M')
        meeting_link = f"{settings.FRONTEND_URL}/meetings/{meeting.id}"

        host = await self.repo.get_user_by_id(host_id)
        host_name = host.full_name if host else "Host"
        host_email = host.email if host else None

        # Build invited participants list string
        invited_names = "\n".join(
            f"  - {invite.name} ({invite.email})"
            for invite in payload.invitations
        )

        # Send host confirmation email
        host_subject = f"Meeting Scheduled: {meeting.title}"
        host_body = (
            f"Hello {host_name},\n\n"
            f"Your meeting has been scheduled successfully.\n\n"
            f"Title: {meeting.title}\n"
            f"Description: {meeting.description or 'No description provided'}\n"
            f"Date: {formatted_date}\n"
            f"Time: {formatted_time}\n"
            f"Timezone: {payload.timezone}\n"
            f"Meeting Link: {meeting_link}\n\n"
            f"Invited Participants:\n{invited_names}\n\n"
            f"You can manage this meeting from your dashboard."
        )

        if host_email:
            try:
                send_async_email.delay(
                    recipient=host_email,
                    subject=host_subject,
                    body=host_body
                )
            except Exception as e:
                logger.error(f"Failed to send host invitation email for meeting {meeting.id}: {e}")

        # Send participant invitations
        for invite in payload.invitations:
            db_invite = await self.repo.create_invitation(meeting.id, invite.model_dump())

            participant_subject = f"Invitation: {meeting.title}"
            participant_body = (
                f"Hello {db_invite.name},\n\n"
                f"You have been invited to a meeting by {host_name}.\n\n"
                f"Title: {meeting.title}\n"
                f"Date: {formatted_date}\n"
                f"Time: {formatted_time}\n"
                f"Timezone: {payload.timezone}\n"
                f"Agenda: {meeting.agenda or 'No agenda provided'}\n"
                f"Meeting Link: {meeting_link}\n\n"
                f"See you there!"
            )

            try:
                send_async_email.delay(
                    recipient=db_invite.email,
                    subject=participant_subject,
                    body=participant_body
                )
            except Exception as e:
                logger.error(f"Failed to send invitation email to {db_invite.email} for meeting {meeting.id}: {e}")

        meeting.invited_participants_count = len(payload.invitations)
        return meeting

    async def list_meeting_invitations(self, meeting_id: UUID, user_id: UUID) -> Sequence[MeetingInvitation]:
        meeting = await self.get_meeting(meeting_id)
        if meeting.host_id != user_id:
            raise MeetingAccessDeniedException(meeting_id, user_id)
        return await self.repo.list_invitations(meeting_id)

    async def add_invitations(self, user_id: UUID, meeting_id: UUID, invites: List[InvitationCreate]) -> List[MeetingInvitation]:
        meeting = await self.get_meeting(meeting_id)
        if meeting.host_id != user_id:
            raise MeetingAccessDeniedException(meeting_id, user_id)

        created_invites = []
        for invite in invites:
            existing = await self.repo.get_invitation_by_email(meeting_id, invite.email)
            if not existing:
                new_invite = await self.repo.create_invitation(meeting_id, invite.model_dump())
                created_invites.append(new_invite)

                try:
                    # Trigger emails for ad-hoc invitations added after meeting creation
                    email_subject = f"Invitation Update: {meeting.title}"
                    email_body = (
                        f"Hello {new_invite.name},\n\n"
                        f"You have been added to the meeting: {meeting.title}.\n\n"
                        f"Link to join: {settings.FRONTEND_URL}/meetings/{meeting.id}\n"
                    )

                    send_async_email.delay(
                        recipient=new_invite.email,
                        subject=email_subject,
                        body=email_body
                    )
                except Exception as e:
                    logger.error(f"Failed to send invitation email to {new_invite.email} for meeting {meeting.id}: {e}")

        return created_invites

class MeetingAIAnalysisService:
    def __init__(self, repo: MeetingAIAnalysisRepository, provider: AIProviderService):
        self.repo = repo
        self.provider = provider

    async def get_analysis(self, session_id: UUID) -> MeetingAIAnalysis:
        analysis = await self.repo.get_by_session_id(session_id)
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No AI analysis record found for this meeting session."
            )
        if analysis.status != AIAnalysisStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Analysis is not ready. Current tracking state: '{analysis.status}'."
            )
        return analysis

    async def get_analysis_status(self, session_id: UUID) -> MeetingAIAnalysis:
        analysis = await self.repo.get_by_session_id(session_id)
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No AI telemetry tracking footprint found for this identifier."
            )
        return analysis

    async def process_async_transcript_analysis(self, session_id: UUID, agenda: str, transcript_text: str) -> None:
        """
        Executed out-of-process inside the Celery worker pool.
        Handles status updates and persists analysis results only.
        """
        analysis = await self.repo.get_by_session_id(session_id)
        if not analysis:
            analysis = await self.repo.create_analysis_placeholder(session_id)

        await self.repo.update_status(analysis.id, AIAnalysisStatus.PROCESSING)

        try:
            result = await self.provider.generate_transcript_analysis(agenda, transcript_text)
            parsed = result["parsed"]

            await self.repo.update_status(
                analysis_id=analysis.id,
                status=AIAnalysisStatus.COMPLETED,
                summary=parsed["summary"],
                agenda_coverage_percentage=parsed["coverage_percentage"],
                covered_points=parsed["covered_points"],
                out_of_agenda_points=parsed["out_of_agenda_points"],
                suggested_tasks=parsed["suggested_tasks"],
                raw_response=result["raw"]
            )

        except Exception as e:
            await self.repo.update_status(
                analysis.id,
                AIAnalysisStatus.FAILED,
                raw_response={"error_log_payload": str(e)}
            )
            raise e


class MeetingSessionService:
    def __init__(self, repo: MeetingSessionRepository, redis: Redis, meeting_repo=None):
        self.repo = repo
        self.redis = redis
        self._meeting_repo = meeting_repo  # injected for session history queries

    async def create_session(self, meeting_id: UUID, host_id: UUID) -> MeetingSession:
        session = await self.repo.create_session(meeting_id, host_id)
        await self._init_redis_state(session)
        return session

    async def finish_session(self, session_id: UUID) -> MeetingSession | None:
        session = await self.repo.finish_session(session_id, status=SessionStatus.ENDED)
        if session:
            await self._clear_redis_state(session.meeting_id)
        return session

    async def get_active_session(self, meeting_id: UUID) -> MeetingSession | None:
        redis_data = await self._get_redis_session(meeting_id)
        if redis_data:
            session_id = UUID(redis_data["session_id"])
            session = await self.repo.get_by_id(session_id)
            if session and session.status == SessionStatus.ACTIVE:
                return session
            await self._clear_redis_state(meeting_id)
        session = await self.repo.get_active_session(meeting_id)
        if session:
            await self._init_redis_state(session)
        return session

    async def remove_live_state(self, meeting_id: UUID) -> None:
        await self._clear_redis_state(meeting_id)

    async def list_sessions_for_user(
        self,
        meeting_id: UUID,
        user_id: UUID,
        host_id: UUID,
    ) -> list:
        """
        Return all sessions a user is entitled to see:
        - Host → all sessions for the meeting (ordered newest first).
        - Registered participant → only sessions they actually attended.
        Guests never have session history (caller must gate on user_id != None).
        """
        from app.modules.meetings.repository import MeetingRepository
        is_host = (user_id == host_id)
        if is_host:
            sessions = await self.repo.get_sessions_for_meeting(meeting_id)
        else:
            # get_sessions_for_user lives on MeetingRepository, not MeetingSessionRepository
            # We need a MeetingRepository reference — passed via the auth service repo
            meeting_repo: MeetingRepository = self._meeting_repo
            sessions = await meeting_repo.get_sessions_for_user(meeting_id, user_id)

        result = []
        for session in sessions:
            count = await self.repo.count_participants_for_session(session.id)
            session.participant_count = count
            result.append(session)
        return result

    async def get_session_detail(
        self,
        meeting_id: UUID,
        session_id: UUID,
        user_id: UUID,
        host_id: UUID,
    ):
        """
        Return a single session's detail if the user has access.
        Raises SessionAccessDeniedException if they don't.
        """
        from app.modules.meetings.exceptions import SessionAccessDeniedException

        session = await self.repo.get_by_id(session_id)
        if not session or session.meeting_id != meeting_id:
            raise SessionAccessDeniedException(session_id, user_id)

        is_host = (user_id == host_id)
        if not is_host:
            # participant must have attended this session
            meeting_repo = self._meeting_repo
            participant = await meeting_repo.get_last_participant(session_id, user_id=user_id)
            if not participant:
                raise SessionAccessDeniedException(session_id, user_id)

        participants = await self.repo.get_participants_for_session(session_id)
        session.participants = participants
        return session

    async def _init_redis_state(self, session: MeetingSession) -> None:
        key = f"meeting:{session.meeting_id}"
        await self.redis.hset(key, mapping={
            "session_id": str(session.id),
            "status": session.status.value,
            "host_id": str(session.host_id),
            "started_at": session.started_at.isoformat(),
        })

    async def _get_redis_session(self, meeting_id: UUID) -> dict | None:
        key = f"meeting:{meeting_id}"
        data = await self.redis.hgetall(key)
        if not data:
            return None
        return {k.decode(): v.decode() for k, v in data.items()}

    async def _clear_redis_state(self, meeting_id: UUID) -> None:
        key = f"meeting:{meeting_id}"
        await self.redis.delete(key)
