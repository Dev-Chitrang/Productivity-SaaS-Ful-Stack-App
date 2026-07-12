from typing import Optional, Set
from uuid import UUID

from app.modules.meetings.repository import MeetingRepository, MeetingSessionRepository
from app.modules.meetings.exceptions import SessionAccessDeniedException


class SessionAuthorizationService:
    def __init__(self, repo: MeetingRepository, session_repo: MeetingSessionRepository):
        self.repo = repo
        self.session_repo = session_repo

    async def verify_session_access(
        self, session_id: UUID, user_id: Optional[UUID], meeting_id: UUID
    ) -> None:
        if not await self._can_access_session(session_id, user_id, meeting_id):
            raise SessionAccessDeniedException(session_id, user_id)

    async def can_access_session(
        self, session_id: UUID, user_id: Optional[UUID], meeting_id: UUID
    ) -> bool:
        return await self._can_access_session(session_id, user_id, meeting_id)

    async def _can_access_session(
        self, session_id: UUID, user_id: Optional[UUID], meeting_id: UUID
    ) -> bool:
        if user_id is None:
            return False

        meeting = await self.repo.get_by_id(meeting_id)
        if not meeting:
            return False
        if meeting.host_id == user_id:
            return True

        participant = await self.repo.get_last_participant(session_id, user_id=user_id)
        return participant is not None

    async def get_accessible_session_ids(
        self, user_id: Optional[UUID], meeting_id: UUID
    ) -> Set[UUID]:
        if user_id is None:
            return set()

        meeting = await self.repo.get_by_id(meeting_id)
        if not meeting:
            return set()
        if meeting.host_id == user_id:
            sessions = await self.session_repo.get_sessions_for_meeting(meeting_id)
            return {s.id for s in sessions}

        sessions = await self.repo.get_sessions_for_user(meeting_id, user_id)
        return {s.id for s in sessions}
