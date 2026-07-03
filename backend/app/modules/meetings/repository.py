import secrets
from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models.meetings import Meeting, MeetingParticipant, MeetingRecording, MeetingTranscript, MeetingInvitation
from app.modules.meetings.enums import MeetingStatus, ParticipantType, ParticipantStatus
from app.modules.meetings.constants import MEETING_URL_FORMAT

class MeetingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def generate_meeting_code(self) -> str:
        """Generates a secure, distinct 10-character meeting code (abc-defg-hij)."""
        part1 = secrets.token_urlsafe(3)[:3].lower()
        part2 = secrets.token_urlsafe(4)[:4].lower()
        part3 = secrets.token_urlsafe(3)[:3].lower()
        return f"{part1}-{part2}-{part3}"

    async def create(self, host_id: UUID, data: dict) -> Meeting:
        try:
            code = self.generate_meeting_code()
            # Ensure unique collision clearance for links
            link = MEETING_URL_FORMAT.format(code=code)

            meeting = Meeting(
                host_id=host_id,
                meeting_code=code,
                meeting_link=link,
                **data
            )
            self.db.add(meeting)
            await self.db.flush()
            return meeting
        except Exception:
            await self.db.rollback()
            raise

    async def get_by_id(self, meeting_id: UUID, include_deleted: bool = False) -> Optional[Meeting]:
        stmt = select(Meeting).where(Meeting.id == meeting_id)
        if not include_deleted:
            stmt = stmt.where(Meeting.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str, include_deleted: bool = False) -> Optional[Meeting]:
        stmt = select(Meeting).where(func.lower(Meeting.meeting_code) == code.strip().lower())
        if not include_deleted:
            stmt = stmt.where(Meeting.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_name_by_id(self, user_id: UUID) -> Optional[str]:
        from app.models.user import User
        stmt = select(User.full_name).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, meeting: Meeting, update_data: dict) -> Meeting:
        try:
            for key, value in update_data.items():
                setattr(meeting, key, value)
            self.db.add(meeting)
            await self.db.flush()
            return meeting
        except Exception:
            await self.db.rollback()
            raise

    async def list_user_meetings(self, user_id: UUID) -> Sequence[Meeting]:
        stmt = select(Meeting).where(
            Meeting.host_id == user_id,
            Meeting.deleted_at.is_(None)
        ).order_by(Meeting.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create_participant(
        self,
        meeting_id: UUID,
        user_id: Optional[UUID],
        guest_name: Optional[str],
        guest_email: Optional[str],
        p_type: ParticipantType,
        status: ParticipantStatus = ParticipantStatus.WAITING
    ) -> MeetingParticipant:
        try:
            participant = MeetingParticipant(
                meeting_id=meeting_id,
                user_id=user_id,
                guest_name=guest_name,
                guest_email=guest_email,
                participant_type=p_type,
                status=status,
                is_muted=False
            )
            self.db.add(participant)
            await self.db.flush()
            return participant
        except Exception:
            await self.db.rollback()
            raise

    async def get_participant_by_id(self, participant_id: UUID) -> Optional[MeetingParticipant]:
        stmt = select(MeetingParticipant).where(MeetingParticipant.id == participant_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_participant(self, meeting_id: UUID, user_id: Optional[UUID] = None, guest_email: Optional[str] = None) -> Optional[MeetingParticipant]:
        conditions = [MeetingParticipant.meeting_id == meeting_id, MeetingParticipant.left_at.is_(None), MeetingParticipant.status.notin_([ParticipantStatus.LEFT, ParticipantStatus.REMOVED, ParticipantStatus.REJECTED])]
        if user_id:
            conditions.append(MeetingParticipant.user_id == user_id)
        elif guest_email:
            conditions.append(MeetingParticipant.guest_email == guest_email)
        else:
            return None

        stmt = select(MeetingParticipant).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_last_participant(self, meeting_id: UUID, user_id: Optional[UUID] = None, guest_email: Optional[str] = None) -> Optional[MeetingParticipant]:
        conditions = [MeetingParticipant.meeting_id == meeting_id]
        if user_id:
            conditions.append(MeetingParticipant.user_id == user_id)
        elif guest_email:
            conditions.append(MeetingParticipant.guest_email == guest_email)
        else:
            return None

        stmt = select(MeetingParticipant).where(and_(*conditions)).order_by(MeetingParticipant.joined_at.desc())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_participants_list(self, meeting_id: UUID, active_only: bool = True) -> Sequence[MeetingParticipant]:
        from app.models.user import User
        conditions = [MeetingParticipant.meeting_id == meeting_id]
        if active_only:
            conditions.append(MeetingParticipant.status.in_([ParticipantStatus.WAITING, ParticipantStatus.ADMITTED]))
        stmt = (
            select(MeetingParticipant, User.full_name)
            .outerjoin(User, MeetingParticipant.user_id == User.id)
            .where(and_(*conditions))
            .order_by(MeetingParticipant.joined_at.asc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        # Attach user_name as a transient attribute for response serialization
        for participant, full_name in rows:
            participant.user_name = full_name
        return [row[0] for row in rows]

    async def add_recording(self, recording_data: dict) -> MeetingRecording:
        rec = MeetingRecording(**recording_data)
        self.db.add(rec)
        await self.db.flush()
        return rec

    async def add_transcript(self, transcript_data: dict) -> MeetingTranscript:
        tx = MeetingTranscript(**transcript_data)
        self.db.add(tx)
        await self.db.flush()
        return tx

    async def get_recording_by_id(self, rec_id: UUID) -> Optional[MeetingRecording]:
        stmt = select(MeetingRecording).where(MeetingRecording.id == rec_id)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_transcript_by_id(self, tx_id: UUID) -> Optional[MeetingTranscript]:
        stmt = select(MeetingTranscript).where(MeetingTranscript.id == tx_id)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_recordings_by_meeting(self, meeting_id: UUID) -> Sequence[MeetingRecording]:
        stmt = select(MeetingRecording).where(MeetingRecording.meeting_id == meeting_id).order_by(MeetingRecording.created_at.asc())
        return (await self.db.execute(stmt)).scalars().all()

    async def list_transcripts_by_meeting(self, meeting_id: UUID) -> Sequence[MeetingTranscript]:
        stmt = select(MeetingTranscript).where(MeetingTranscript.meeting_id == meeting_id).order_by(MeetingTranscript.created_at.asc())
        return (await self.db.execute(stmt)).scalars().all()

    async def delete_recording_meta(self, rec: MeetingRecording) -> None:
        await self.db.delete(rec)
        await self.db.flush()

    async def delete_transcript_meta(self, tx: MeetingTranscript) -> None:
        await self.db.delete(tx)
        await self.db.flush()

    async def update_participant(self, participant: MeetingParticipant, update_data: dict) -> MeetingParticipant:
        try:
            for key, value in update_data.items():
                setattr(participant, key, value)
            self.db.add(participant)
            await self.db.flush()
            return participant
        except Exception:
            await self.db.rollback()
            raise

    async def soft_delete(self, meeting: Meeting) -> None:
        try:
            meeting.deleted_at = datetime.now(timezone.utc)
            self.db.add(meeting)
            await self.db.flush()
        except Exception:
            await self.db.rollback()
            raise

    async def restore(self, meeting: Meeting) -> Meeting:
        try:
            meeting.deleted_at = None
            self.db.add(meeting)
            await self.db.flush()
            return meeting
        except Exception:
            await self.db.rollback()
            raise

    async def get_meeting_status(self, meeting_id: UUID) -> Optional[MeetingStatus]:
        stmt = select(Meeting.status).where(Meeting.id == meeting_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_invitation(self, meeting_id: UUID, data: dict) -> MeetingInvitation:
        invitation = MeetingInvitation(meeting_id=meeting_id, **data)
        self.db.add(invitation)
        await self.db.flush()
        return invitation

    async def get_invitation_by_email(self, meeting_id: UUID, email: str) -> Optional[MeetingInvitation]:
        stmt = select(MeetingInvitation).where(
            and_(
                MeetingInvitation.meeting_id == meeting_id,
                func.lower(MeetingInvitation.email) == email.strip().lower()
            )
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def count_invitations(self, meeting_id: UUID) -> int:
        stmt = select(func.count(MeetingInvitation.id)).where(MeetingInvitation.meeting_id == meeting_id)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def get_user_by_id(self, user_id: UUID) -> Optional["User"]:
        from app.models.user import User
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_invitations(self, meeting_id: UUID) -> Sequence[MeetingInvitation]:
        stmt = select(MeetingInvitation).where(MeetingInvitation.meeting_id == meeting_id).order_by(MeetingInvitation.name.asc())
        return (await self.db.execute(stmt)).scalars().all()
