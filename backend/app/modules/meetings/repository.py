import secrets
from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update, case
from app.models.meetings import Meeting, MeetingParticipant, MeetingRecording, MeetingTranscript, MeetingInvitation, MeetingAIAnalysis, MeetingSession
from app.modules.meetings.enums import MeetingStatus, ParticipantType, ParticipantStatus, SessionStatus, AIAnalysisStatus
from app.modules.meetings.constants import MEETING_URL_FORMAT

class MeetingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def generate_meeting_code(self) -> str:
        part1 = secrets.token_urlsafe(3)[:3].lower()
        part2 = secrets.token_urlsafe(4)[:4].lower()
        part3 = secrets.token_urlsafe(3)[:3].lower()
        return f"{part1}-{part2}-{part3}"

    async def create(self, host_id: UUID, data: dict) -> Meeting:
        try:
            code = self.generate_meeting_code()
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
        session_id: UUID,
        user_id: Optional[UUID],
        guest_name: Optional[str],
        guest_email: Optional[str],
        p_type: ParticipantType,
        status: ParticipantStatus = ParticipantStatus.WAITING
    ) -> MeetingParticipant:
        try:
            participant = MeetingParticipant(
                session_id=session_id,
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

    async def get_active_participant(self, session_id: UUID, user_id: Optional[UUID] = None, guest_email: Optional[str] = None) -> Optional[MeetingParticipant]:
        conditions = [MeetingParticipant.session_id == session_id, MeetingParticipant.left_at.is_(None), MeetingParticipant.status.notin_([ParticipantStatus.LEFT, ParticipantStatus.REMOVED, ParticipantStatus.REJECTED])]
        if user_id:
            conditions.append(MeetingParticipant.user_id == user_id)
        elif guest_email:
            conditions.append(MeetingParticipant.guest_email == guest_email)
        else:
            return None

        stmt = select(MeetingParticipant).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_last_participant(self, session_id: UUID, user_id: Optional[UUID] = None, guest_email: Optional[str] = None) -> Optional[MeetingParticipant]:
        conditions = [MeetingParticipant.session_id == session_id]
        if user_id:
            conditions.append(MeetingParticipant.user_id == user_id)
        elif guest_email:
            conditions.append(MeetingParticipant.guest_email == guest_email)
        else:
            return None

        stmt = select(MeetingParticipant).where(and_(*conditions)).order_by(MeetingParticipant.joined_at.desc())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_participants_by_session(self, session_id: UUID, active_only: bool = True) -> Sequence[MeetingParticipant]:
        from app.models.user import User
        conditions = [MeetingParticipant.session_id == session_id]
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
        for participant, full_name in rows:
            participant.user_name = full_name
        return [row[0] for row in rows]

    async def get_participants_by_meeting(self, meeting_id: UUID, active_only: bool = True) -> Sequence[MeetingParticipant]:
        from app.models.user import User
        conditions = [MeetingParticipant.session_id == MeetingSession.id, MeetingSession.meeting_id == meeting_id]
        if active_only:
            conditions.append(MeetingParticipant.status.in_([ParticipantStatus.WAITING, ParticipantStatus.ADMITTED]))
        stmt = (
            select(MeetingParticipant, User.full_name)
            .outerjoin(User, MeetingParticipant.user_id == User.id)
            .join(MeetingSession, MeetingParticipant.session_id == MeetingSession.id)
            .where(and_(*conditions))
            .order_by(MeetingParticipant.joined_at.asc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()
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

    async def list_recordings_by_session(self, session_id: UUID) -> Sequence[MeetingRecording]:
        stmt = select(MeetingRecording).where(MeetingRecording.session_id == session_id).order_by(MeetingRecording.created_at.asc())
        return (await self.db.execute(stmt)).scalars().all()

    async def list_transcripts_by_session(self, session_id: UUID) -> Sequence[MeetingTranscript]:
        stmt = select(MeetingTranscript).where(MeetingTranscript.session_id == session_id).order_by(MeetingTranscript.created_at.asc())
        return (await self.db.execute(stmt)).scalars().all()

    async def list_recordings_by_meeting(self, meeting_id: UUID) -> Sequence[MeetingRecording]:
        stmt = (
            select(MeetingRecording)
            .join(MeetingSession, MeetingRecording.session_id == MeetingSession.id)
            .where(MeetingSession.meeting_id == meeting_id)
            .order_by(MeetingRecording.created_at.asc())
        )
        return (await self.db.execute(stmt)).scalars().all()

    async def list_transcripts_by_meeting(self, meeting_id: UUID) -> Sequence[MeetingTranscript]:
        stmt = (
            select(MeetingTranscript)
            .join(MeetingSession, MeetingTranscript.session_id == MeetingSession.id)
            .where(MeetingSession.meeting_id == meeting_id)
            .order_by(MeetingTranscript.created_at.asc())
        )
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

    async def bulk_end_participants(
        self,
        meeting_id: UUID,
        now: datetime,
        screen_sharer_id: Optional[UUID] = None,
    ) -> int:
        values = {
            "status": ParticipantStatus.LEFT,
            "left_at": now,
        }
        if screen_sharer_id is not None:
            values["can_start_screen_share"] = case(
                (MeetingParticipant.id == screen_sharer_id, False),
                else_=MeetingParticipant.can_start_screen_share,
            )
        stmt = (
            update(MeetingParticipant)
            .where(
                MeetingParticipant.session_id == MeetingSession.id,
                MeetingSession.meeting_id == meeting_id,
                MeetingParticipant.status.notin_([
                    ParticipantStatus.LEFT,
                    ParticipantStatus.REMOVED,
                    ParticipantStatus.REJECTED,
                ]),
            )
            .values(**values)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount

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

    async def get_participants_by_session_ids(self, session_ids: set[UUID]) -> Sequence[MeetingParticipant]:
        from app.models.user import User
        stmt = (
            select(MeetingParticipant, User.full_name)
            .outerjoin(User, MeetingParticipant.user_id == User.id)
            .where(MeetingParticipant.session_id.in_(session_ids))
            .order_by(MeetingParticipant.joined_at.asc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        for participant, full_name in rows:
            participant.user_name = full_name
        return [row[0] for row in rows]

    async def get_sessions_for_user(self, meeting_id: UUID, user_id: UUID) -> Sequence[MeetingSession]:
        stmt = (
            select(MeetingSession)
            .join(MeetingParticipant, MeetingParticipant.session_id == MeetingSession.id)
            .where(
                MeetingSession.meeting_id == meeting_id,
                MeetingParticipant.user_id == user_id,
            )
            .distinct()
            .order_by(MeetingSession.started_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_session_by_recording_id(self, rec_id: UUID) -> Optional[MeetingSession]:
        stmt = (
            select(MeetingSession)
            .join(MeetingRecording, MeetingRecording.session_id == MeetingSession.id)
            .where(MeetingRecording.id == rec_id)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_session_by_transcript_id(self, tx_id: UUID) -> Optional[MeetingSession]:
        stmt = (
            select(MeetingSession)
            .join(MeetingTranscript, MeetingTranscript.session_id == MeetingSession.id)
            .where(MeetingTranscript.id == tx_id)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_meeting_by_recording_id(self, rec_id: UUID) -> Optional[Meeting]:
        stmt = (
            select(Meeting)
            .join(MeetingSession, MeetingSession.meeting_id == Meeting.id)
            .join(MeetingRecording, MeetingRecording.session_id == MeetingSession.id)
            .where(MeetingRecording.id == rec_id)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_meeting_by_transcript_id(self, tx_id: UUID) -> Optional[Meeting]:
        stmt = (
            select(Meeting)
            .join(MeetingSession, MeetingSession.meeting_id == Meeting.id)
            .join(MeetingTranscript, MeetingTranscript.session_id == MeetingSession.id)
            .where(MeetingTranscript.id == tx_id)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_recordings_by_session_ids(self, session_ids: set[UUID]) -> Sequence[MeetingRecording]:
        stmt = (
            select(MeetingRecording)
            .where(MeetingRecording.session_id.in_(session_ids))
            .order_by(MeetingRecording.created_at.asc())
        )
        return (await self.db.execute(stmt)).scalars().all()

    async def list_transcripts_by_session_ids(self, session_ids: set[UUID]) -> Sequence[MeetingTranscript]:
        stmt = (
            select(MeetingTranscript)
            .where(MeetingTranscript.session_id.in_(session_ids))
            .order_by(MeetingTranscript.created_at.asc())
        )
        return (await self.db.execute(stmt)).scalars().all()


class MeetingAIAnalysisRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_analysis_placeholder(self, session_id: UUID) -> MeetingAIAnalysis:
        analysis = MeetingAIAnalysis(
            session_id=session_id,
            status=AIAnalysisStatus.PENDING
        )
        self.db.add(analysis)
        await self.db.flush()
        return analysis

    async def get_by_session_id(self, session_id: UUID) -> Optional[MeetingAIAnalysis]:
        stmt = (
            select(MeetingAIAnalysis)
            .where(MeetingAIAnalysis.session_id == session_id)
            .order_by(MeetingAIAnalysis.created_at.desc())
            .limit(1)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_by_meeting_id(self, meeting_id: UUID) -> Optional[MeetingAIAnalysis]:
        stmt = (
            select(MeetingAIAnalysis)
            .join(MeetingSession, MeetingAIAnalysis.session_id == MeetingSession.id)
            .where(MeetingSession.meeting_id == meeting_id)
            .order_by(MeetingAIAnalysis.created_at.desc())
            .limit(1)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_recent_for_user(self, user_id: UUID, limit: int = 5) -> Sequence[tuple]:
        stmt = (
            select(
                MeetingAIAnalysis.id,
                MeetingAIAnalysis.session_id,
                MeetingAIAnalysis.status,
                MeetingAIAnalysis.summary,
                MeetingAIAnalysis.agenda_coverage_percentage,
                MeetingAIAnalysis.processing_completed_at,
                MeetingAIAnalysis.created_at,
                Meeting.id.label("meeting_id"),
                Meeting.title.label("meeting_title"),
                MeetingSession.started_at.label("session_date"),
            )
            .join(MeetingSession, MeetingAIAnalysis.session_id == MeetingSession.id)
            .join(Meeting, MeetingSession.meeting_id == Meeting.id)
            .where(
                and_(
                    Meeting.host_id == user_id,
                    MeetingAIAnalysis.status == AIAnalysisStatus.COMPLETED,
                )
            )
            .order_by(MeetingAIAnalysis.processing_completed_at.desc().nulls_last())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.all()

    async def update_status(self, analysis_id: UUID, status: AIAnalysisStatus, **kwargs) -> None:
        payload = {"status": status, "updated_at": datetime.now(timezone.utc)}
        if status == AIAnalysisStatus.PROCESSING:
            payload["processing_started_at"] = datetime.now(timezone.utc)
        elif status in [AIAnalysisStatus.COMPLETED, AIAnalysisStatus.FAILED]:
            payload["processing_completed_at"] = datetime.now(timezone.utc)

        payload.update(kwargs)

        stmt = update(MeetingAIAnalysis).where(MeetingAIAnalysis.id == analysis_id).values(**payload)
        await self.db.execute(stmt)
        await self.db.flush()


class MeetingSessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, meeting_id: UUID, host_id: UUID) -> MeetingSession:
        session = MeetingSession(
            meeting_id=meeting_id,
            host_id=host_id,
            status=SessionStatus.ACTIVE,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_by_id(self, session_id: UUID) -> MeetingSession | None:
        stmt = select(MeetingSession).where(MeetingSession.id == session_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_session(self, meeting_id: UUID) -> MeetingSession | None:
        stmt = (
            select(MeetingSession)
            .where(
                MeetingSession.meeting_id == meeting_id,
                MeetingSession.status == SessionStatus.ACTIVE,
            )
            .order_by(MeetingSession.started_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_sessions_for_meeting(self, meeting_id: UUID) -> Sequence[MeetingSession]:
        stmt = (
            select(MeetingSession)
            .where(MeetingSession.meeting_id == meeting_id)
            .order_by(MeetingSession.started_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update(self, session: MeetingSession, update_data: dict) -> MeetingSession:
        try:
            for key, value in update_data.items():
                setattr(session, key, value)
            self.db.add(session)
            await self.db.flush()
            return session
        except Exception:
            await self.db.rollback()
            raise

    async def finish_session(
        self,
        session_id: UUID,
        status: SessionStatus = SessionStatus.ENDED,
    ) -> MeetingSession | None:
        session = await self.get_by_id(session_id)
        if not session:
            return None
        now = datetime.now(timezone.utc)
        duration = int((now - session.started_at).total_seconds()) if session.started_at else None
        return await self.update(session, {
            "status": status,
            "ended_at": now,
            "duration_seconds": duration,
        })

    async def count_participants_for_session(self, session_id: UUID) -> int:
        """Count distinct users (registered) and guests that participated in a session."""
        stmt = select(func.count(MeetingParticipant.id)).where(
            MeetingParticipant.session_id == session_id
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def get_participants_for_session(self, session_id: UUID) -> Sequence[MeetingParticipant]:
        """Return all participants for a session including user names."""
        from app.models.user import User
        stmt = (
            select(MeetingParticipant, User.full_name)
            .outerjoin(User, MeetingParticipant.user_id == User.id)
            .where(MeetingParticipant.session_id == session_id)
            .order_by(MeetingParticipant.joined_at.asc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        for participant, full_name in rows:
            participant.user_name = full_name
        return [row[0] for row in rows]
