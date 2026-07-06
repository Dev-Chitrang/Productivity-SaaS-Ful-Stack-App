from typing import Optional, Sequence, List
from uuid import UUID

from sqlalchemy import select

from app.modules.entity_links.repository import EntityLinkRepository
from app.models.entity_link import EntityLink
from app.modules.entity_links.schemas import EntityLinkCreate
from app.modules.entity_links.enums import EntityType, RelationOrigin
from app.modules.entity_links.exceptions import (
    EntityLinkNotFoundException,
    EntityLinkAccessDeniedException,
    EntityLinkValidationError,
)
from app.models.tasks import Task
from app.models.meetings import Meeting, MeetingSession


class EntityLinkService:
    def __init__(self, repo: EntityLinkRepository):
        self.repo = repo

    async def create_link(self, user_id: UUID, payload: EntityLinkCreate) -> EntityLink:
        if payload.source_type == payload.target_type and payload.source_id == payload.target_id:
            raise EntityLinkValidationError("Cannot link an entity to itself.")

        link_data = payload.model_dump()
        link_data["created_by"] = user_id
        return await self.repo.create(link_data)

    async def get_link(self, user_id: UUID, link_id: UUID) -> EntityLink:
        link = await self.repo.get_by_id(link_id)
        if not link:
            raise EntityLinkNotFoundException(link_id)
        if link.created_by != user_id:
            raise EntityLinkAccessDeniedException(link_id, user_id)
        return link

    async def delete_link(self, user_id: UUID, link_id: UUID) -> None:
        link = await self.get_link(user_id, link_id)
        await self.repo.soft_delete(link)

    async def list_links(
        self,
        user_id: UUID,
        source_type: Optional[str] = None,
        source_id: Optional[UUID] = None,
        target_type: Optional[str] = None,
        target_id: Optional[UUID] = None,
    ) -> Sequence[EntityLink]:
        links = await self.repo.list_links(
            source_type=source_type,
            source_id=source_id,
            target_type=target_type,
            target_id=target_id,
        )
        return [l for l in links if l.created_by == user_id]

    async def get_linked_tasks(self, user_id: UUID, meeting_id: UUID) -> List[dict]:
        links = await self.repo.list_links(
            source_type="meeting",
            source_id=meeting_id,
            target_type="task",
        )
        links = [l for l in links if l.created_by == user_id]

        links_from_target = await self.repo.list_links(
            source_type="task",
            target_type="meeting",
            target_id=meeting_id,
        )
        links_from_target = [l for l in links_from_target if l.created_by == user_id]

        all_links = links + links_from_target
        if not all_links:
            return []

        task_link_map = {}
        for link in all_links:
            if link.source_type == "task":
                task_link_map[link.source_id] = link.id
            else:
                task_link_map[link.target_id] = link.id

        tasks = []
        for task_id in task_link_map:
            result = await self.repo.db.execute(
                select(Task).where(Task.id == task_id, Task.deleted_at.is_(None))
            )
            task = result.scalar_one_or_none()
            if task and task.user_id == user_id:
                tasks.append({
                    "id": task.id,
                    "title": task.title,
                    "priority": task.priority.value if task.priority else "MEDIUM",
                    "status": task.status.value if task.status else "TODO",
                    "due_date": task.due_date,
                    "link_id": task_link_map[task_id],
                })

        return tasks

    async def get_linked_meetings(self, user_id: UUID, task_id: UUID) -> List[dict]:
        # task → meeting (outgoing)
        links_tm = await self.repo.list_links(
            source_type="task",
            source_id=task_id,
            target_type="meeting",
        )
        # meeting → task (incoming)
        links_mt = await self.repo.list_links(
            source_type="meeting",
            target_type="task",
            target_id=task_id,
        )
        # task → meeting_session (outgoing)
        links_ts = await self.repo.list_links(
            source_type="task",
            source_id=task_id,
            target_type="meeting_session",
        )
        # meeting_session → task (incoming)
        links_st = await self.repo.list_links(
            source_type="meeting_session",
            target_type="task",
            target_id=task_id,
        )

        all_links = [
            l for l in (links_tm + links_mt + links_ts + links_st)
            if l.created_by == user_id
        ]
        if not all_links:
            return []

        # Build map: meeting_id → (link_id, session_id or None)
        meeting_entry_map = {}
        for link in all_links:
            if link.target_type == "meeting":
                meeting_entry_map[link.target_id] = (link.id, None)
            elif link.source_type == "meeting":
                meeting_entry_map[link.source_id] = (link.id, None)
            elif link.target_type == "meeting_session":
                meeting_entry_map.setdefault(link.target_id, (link.id, link.target_id))
            elif link.source_type == "meeting_session":
                meeting_entry_map.setdefault(link.source_id, (link.id, link.source_id))

        # Resolve session IDs to meeting IDs
        session_ids = [sid for _, sid in meeting_entry_map.values() if sid is not None]
        meeting_for_session = {}
        if session_ids:
            result = await self.repo.db.execute(
                select(MeetingSession).where(MeetingSession.id.in_(session_ids))
            )
            sessions = result.scalars().all()
            for s in sessions:
                meeting_for_session[s.id] = s.meeting_id

        # Collect unique meeting IDs
        meeting_ids = set()
        raw_links = []
        for entity_id, (link_id, session_id) in meeting_entry_map.items():
            if session_id is not None:
                mid = meeting_for_session.get(entity_id)
                if mid:
                    meeting_ids.add(mid)
                    raw_links.append((mid, link_id, session_id))
            else:
                meeting_ids.add(entity_id)
                raw_links.append((entity_id, link_id, None))

        if not meeting_ids:
            return []

        result = await self.repo.db.execute(
            select(Meeting).where(Meeting.id.in_(meeting_ids), Meeting.deleted_at.is_(None))
        )
        meetings_by_id = {m.id: m for m in result.scalars().all()}

        results = []
        for meeting_id, link_id, session_id in raw_links:
            meeting = meetings_by_id.get(meeting_id)
            if meeting and meeting.host_id == user_id:
                entry = {
                    "id": meeting.id,
                    "title": meeting.title,
                    "status": meeting.status.value if meeting.status else "",
                    "meeting_code": meeting.meeting_code,
                    "scheduled_start": meeting.scheduled_start,
                    "link_id": link_id,
                    "session_id": session_id,
                }
                results.append(entry)

        return results

    async def get_linked_tasks_for_session(self, user_id: UUID, session_id: UUID) -> List[dict]:
        links = await self.repo.list_links(
            source_type="meeting_session",
            source_id=session_id,
            target_type="task",
        )
        links = [l for l in links if l.created_by == user_id]

        links_from_target = await self.repo.list_links(
            source_type="task",
            target_type="meeting_session",
            target_id=session_id,
        )
        links_from_target = [l for l in links_from_target if l.created_by == user_id]

        all_links = links + links_from_target
        if not all_links:
            return []

        task_link_map = {}
        for link in all_links:
            if link.source_type == "task":
                task_link_map[link.source_id] = link.id
            else:
                task_link_map[link.target_id] = link.id

        tasks = []
        for task_id in task_link_map:
            result = await self.repo.db.execute(
                select(Task).where(Task.id == task_id, Task.deleted_at.is_(None))
            )
            task = result.scalar_one_or_none()
            if task and task.user_id == user_id:
                tasks.append({
                    "id": task.id,
                    "title": task.title,
                    "priority": task.priority.value if task.priority else "MEDIUM",
                    "status": task.status.value if task.status else "TODO",
                    "due_date": task.due_date,
                    "link_id": task_link_map[task_id],
                })

        return tasks
