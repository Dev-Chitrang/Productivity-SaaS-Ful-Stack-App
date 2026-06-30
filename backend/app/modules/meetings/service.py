from datetime import datetime, timezone, timedelta
import jwt
from typing import Optional, Sequence
from uuid import UUID

from app.core.storage import StorageService
from app.modules.meetings.repository import MeetingRepository
from app.models.meetings import Meeting, MeetingParticipant, MeetingRecording, MeetingTranscript
from app.modules.meetings.schemas import MeetingCreate, MeetingUpdate
from app.modules.meetings.enums import MeetingStatus, ParticipantType, ParticipantStatus
from app.modules.meetings.exceptions import (
    MeetingNotFoundException,
    MeetingAccessDeniedException,
    MeetingValidationError
)
from app.core.config import settings
from app.core.logger import logger

class MeetingService:
    def __init__(self, repo: MeetingRepository, storage: StorageService):
        self.repo = repo
        self.storage = storage

    async def create_meeting(self, host_id: UUID, payload: MeetingCreate) -> Meeting:
        return await self.repo.create(host_id, payload.model_dump())

    async def get_meeting(self, meeting_id: UUID) -> Meeting:
        meeting = await self.repo.get_by_id(meeting_id)
        if not meeting:
            raise MeetingNotFoundException(meeting_id)
        return meeting

    async def update_meeting(self, user_id: UUID, meeting_id: UUID, payload: MeetingUpdate) -> Meeting:
        meeting = await self.get_meeting(meeting_id)
        if meeting.host_id != user_id:
            raise MeetingAccessDeniedException(meeting_id, user_id)
        if meeting.status == MeetingStatus.CANCELLED:
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

        return await self.repo.update(meeting, {"status": MeetingStatus.IDLE, "ended_at": now, "active_screen_sharer_id": None})

    async def cancel_meeting(self, user_id: UUID, meeting_id: UUID) -> Meeting:
        meeting = await self.get_meeting(meeting_id)
        if meeting.host_id != user_id:
            raise MeetingAccessDeniedException(meeting_id, user_id)
        if meeting.status == MeetingStatus.CANCELLED:
            raise MeetingValidationError(f"Meeting has already reached a terminated '{meeting.status.value}' state.")

        return await self.repo.update(meeting, {"status": MeetingStatus.CANCELLED, "ended_at": datetime.now(timezone.utc), "active_screen_sharer_id": None})

    async def delete_meeting(self, user_id: UUID, meeting_id: UUID) -> Meeting:
        meeting = await self.get_meeting(meeting_id)
        if meeting.host_id != user_id:
            raise MeetingAccessDeniedException(meeting_id, user_id)
        await self.repo.soft_delete(meeting)
        return meeting

    async def get_meeting_by_code(self, code: str) -> tuple:
        meeting = await self.repo.get_by_code(code, include_deleted=True)
        if not meeting:
            raise MeetingNotFoundException(f"Meeting with code '{code}' not found or has been removed.")
        if meeting.deleted_at:
            raise MeetingNotFoundException("This meeting no longer exists.")
        host_name = await self.repo.get_user_name_by_id(meeting.host_id) or "Unknown"
        return meeting, host_name

    async def leave_meeting_flow(self, meeting_id: UUID, user_id: Optional[UUID] = None, guest_email: Optional[str] = None) -> None:
        participant = await self.repo.get_active_participant(meeting_id, user_id=user_id, guest_email=guest_email)
        if participant:
            await self._clear_screen_sharer_if_needed(meeting_id, participant.id)
            await self.repo.update_participant(participant, {
                "status": ParticipantStatus.LEFT,
                "left_at": datetime.now(timezone.utc)
            })
            await self._transition_to_idle_if_empty(meeting_id)

    async def list_participants(self, meeting_id: UUID) -> Sequence[MeetingParticipant]:
        await self.get_meeting(meeting_id)
        return await self.repo.get_participants_list(meeting_id)

    async def save_recording_file(self, meeting_id: UUID, file, duration: Optional[float] = None) -> MeetingRecording:
        await self.get_meeting(meeting_id)

        content = await file.read()
        content_type = file.content_type or "audio/webm"
        result = await self.storage.save_recording(
            meeting_id=meeting_id,
            filename=file.filename or "recording.webm",
            content=content,
            content_type=content_type,
        )

        recording_data = {
            "meeting_id": meeting_id,
            "filename": result["filename"],
            "content_type": content_type,
            "size": result["size"],
            "duration": duration,
            "storage_path": result["storage_path"],
        }
        return await self.repo.add_recording(recording_data)

    async def save_transcript_file(self, meeting_id: UUID, file, content_type: str = "text/plain") -> MeetingTranscript:
        await self.get_meeting(meeting_id)

        content = await file.read()
        result = await self.storage.save_transcript(
            meeting_id=meeting_id,
            filename=file.filename or "transcript.txt",
            content=content,
            content_type=content_type,
        )

        transcript_data = {
            "meeting_id": meeting_id,
            "filename": result["filename"],
            "content_type": content_type,
            "size": result["size"],
            "storage_path": result["storage_path"],
        }
        return await self.repo.add_transcript(transcript_data)

    async def get_recording_artifact(self, rec_id: UUID) -> MeetingRecording:
        rec = await self.repo.get_recording_by_id(rec_id)
        if not rec or not self.storage.exists(rec.storage_path):
            raise MeetingNotFoundException(rec_id)
        return rec

    async def get_transcript_artifact(self, tx_id: UUID) -> MeetingTranscript:
        tx = await self.repo.get_transcript_by_id(tx_id)
        if not tx or not self.storage.exists(tx.storage_path):
            raise MeetingNotFoundException(tx_id)
        return tx

    async def list_recordings(self, meeting_id: UUID) -> Sequence[MeetingRecording]:
        await self.get_meeting(meeting_id)
        return await self.repo.list_recordings_by_meeting(meeting_id)

    async def list_transcripts(self, meeting_id: UUID) -> Sequence[MeetingTranscript]:
        await self.get_meeting(meeting_id)
        return await self.repo.list_transcripts_by_meeting(meeting_id)

    async def remove_recording(self, rec_id: UUID) -> None:
        rec = await self.repo.get_recording_by_id(rec_id)
        if rec:
            await self.storage.delete_file(rec.storage_path)
            await self.repo.delete_recording_meta(rec)

    async def remove_transcript(self, tx_id: UUID) -> None:
        tx = await self.repo.get_transcript_by_id(tx_id)
        if tx:
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

        # Reusable rooms: ENDED or IDLE meetings can be rejoined (reactivate)
        if meeting.status in (MeetingStatus.ENDED, MeetingStatus.IDLE):
            await self.repo.update(meeting, {"status": MeetingStatus.ACTIVE, "ended_at": None})
            meeting.status = MeetingStatus.ACTIVE

        is_host = (user_id is not None and meeting.host_id == user_id)

        if is_host and meeting.status == MeetingStatus.CREATED:
            await self.repo.update(meeting, {"status": MeetingStatus.ACTIVE})
            meeting.status = MeetingStatus.ACTIVE

        initial_status = ParticipantStatus.ADMITTED if is_host else ParticipantStatus.WAITING

        if user_id:
            p_type = ParticipantType.REGISTERED
            existing = await self.repo.get_active_participant(meeting_id, user_id=user_id)
            if existing:
                if existing.status == ParticipantStatus.REMOVED:
                    raise MeetingAccessDeniedException(meeting_id, user_id)
                if is_host and not existing.can_start_screen_share:
                    await self.repo.update_participant(existing, {"can_start_screen_share": True})
                return existing
            # Reuse a LEFT participant record instead of creating a new one
            last = await self.repo.get_last_participant(meeting_id, user_id=user_id)
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
            existing = await self.repo.get_active_participant(meeting_id, guest_email=guest_email)
            if existing:
                if existing.status == ParticipantStatus.REMOVED:
                    raise MeetingValidationError("You have been removed from this meeting room container.")
                if guest_name:
                    await self.repo.update_participant(existing, {"guest_name": guest_name.strip()})
                return existing
            # Reuse a LEFT participant record instead of creating a new one
            last = await self.repo.get_last_participant(meeting_id, guest_email=guest_email)
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
            meeting_id=meeting_id,
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
        if not participant or participant.meeting_id != meeting_id:
            raise MeetingValidationError("Target participant node context matching failed.")

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
        if not participant or participant.meeting_id != meeting_id:
            raise MeetingValidationError("Target participant node context matching failed.")

        participant = await self.repo.update_participant(participant, {"is_muted": mute})
        return participant

    async def _transition_to_idle_if_empty(self, meeting_id: UUID) -> None:
        participants = await self.repo.get_participants_list(meeting_id, active_only=True)
        if len(participants) == 0:
            meeting = await self.repo.get_by_id(meeting_id, include_deleted=True)
            if meeting and meeting.status != MeetingStatus.IDLE:
                await self.repo.update(meeting, {"status": MeetingStatus.IDLE})

    async def leave_meeting(self, meeting_id: UUID, user_id: Optional[UUID] = None, guest_email: Optional[str] = None) -> MeetingParticipant:
        participant = await self.repo.get_active_participant(meeting_id, user_id=user_id, guest_email=guest_email)
        if not participant:
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
        participants = await self.repo.get_participants_list(meeting_id)
        return sum(1 for p in participants if p.status == ParticipantStatus.WAITING)

    async def request_screen_share(self, meeting_id: UUID, participant_id: UUID) -> MeetingParticipant:
        meeting = await self.get_meeting(meeting_id)
        logger.info("[screen_share_request] participant_id=%s participant.status=N/A meeting.status=%s can_start_screen_share=N/A reason=checking_meeting_active", participant_id, meeting.status.value if meeting else "NONE")
        if meeting.status != MeetingStatus.ACTIVE:
            logger.warning("[screen_share_request] REJECTED participant_id=%s meeting.status=%s reason=meeting_not_active", participant_id, meeting.status.value)
            raise MeetingValidationError("Meeting is not active.")
        participant = await self.repo.get_participant_by_id(participant_id)
        logger.info("[screen_share_request] participant_id=%s participant.status=%s meeting.status=%s can_start_screen_share=%s reason=checking_participant_exists", participant_id, participant.status.value if participant else "NOT_FOUND", meeting.status.value, participant.can_start_screen_share if participant else "N/A")
        if not participant or participant.meeting_id != meeting_id:
            logger.warning("[screen_share_request] REJECTED participant_id=%s reason=participant_not_found meeting_id=%s", participant_id, meeting_id)
            raise MeetingValidationError("Participant not found.")
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
        if not participant or participant.meeting_id != meeting_id:
            raise MeetingValidationError("Participant not found.")
        participant = await self.repo.update_participant(participant, {"can_start_screen_share": True})
        return participant

    async def reject_screen_share(self, meeting_id: UUID, host_id: UUID, participant_id: UUID) -> MeetingParticipant:
        meeting = await self.get_meeting(meeting_id)
        if meeting.host_id != host_id:
            raise MeetingAccessDeniedException(meeting_id, host_id)
        participant = await self.repo.get_participant_by_id(participant_id)
        if not participant or participant.meeting_id != meeting_id:
            raise MeetingValidationError("Participant not found.")
        return participant

    async def start_screen_share(self, meeting_id: UUID, participant_id: UUID, user_id: Optional[UUID] = None, guest_name: Optional[str] = None) -> Meeting:
        meeting = await self.get_meeting(meeting_id)
        if meeting.status != MeetingStatus.ACTIVE:
            raise MeetingValidationError("Meeting is not active.")
        if meeting.active_screen_sharer_id is not None:
            raise MeetingValidationError("Another participant is already sharing their screen.")

        participant = await self.repo.get_participant_by_id(participant_id)
        if not participant or participant.meeting_id != meeting_id:
            raise MeetingValidationError("Participant not found.")

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

    @staticmethod
    def generate_meeting_session_token(participant_id: UUID, meeting_id: UUID) -> str:
        payload = {
            "participant_id": str(participant_id),
            "meeting_id": str(meeting_id),
        }
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.MEETING_SESSION_TOKEN_EXPIRE_MINUTES)
        payload["exp"] = int(expire.timestamp())
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
