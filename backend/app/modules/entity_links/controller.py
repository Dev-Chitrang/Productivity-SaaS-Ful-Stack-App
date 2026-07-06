from typing import Optional, List
from uuid import UUID
from fastapi import HTTPException, status

from app.modules.entity_links.services import EntityLinkService
from app.modules.entity_links.schemas import (
    EntityLinkCreate,
    EntityLinkResponse,
    EntityLinkListResponse,
    LinkedTaskResponse,
    LinkedMeetingResponse,
)
from app.modules.entity_links.exceptions import (
    EntityLinkNotFoundException,
    EntityLinkAccessDeniedException,
    EntityLinkValidationError,
)


class EntityLinkController:
    def __init__(self, service: EntityLinkService):
        self.service = service

    async def create_link(self, user_id: UUID, payload: EntityLinkCreate) -> dict:
        try:
            link = await self.service.create_link(user_id, payload)
            return EntityLinkResponse.model_validate(link)
        except EntityLinkValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def delete_link(self, user_id: UUID, link_id: UUID) -> dict:
        try:
            await self.service.delete_link(user_id, link_id)
            return {"status": "success", "message": "Link deleted successfully."}
        except EntityLinkNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except EntityLinkAccessDeniedException as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    async def list_links(
        self,
        user_id: UUID,
        source_type: Optional[str] = None,
        source_id: Optional[UUID] = None,
        target_type: Optional[str] = None,
        target_id: Optional[UUID] = None,
    ) -> dict:
        links = await self.service.list_links(
            user_id,
            source_type=source_type,
            source_id=source_id,
            target_type=target_type,
            target_id=target_id,
        )
        return EntityLinkListResponse(
            links=[EntityLinkResponse.model_validate(l) for l in links],
            total_count=len(links),
        )

    async def get_linked_tasks(self, user_id: UUID, meeting_id: UUID) -> List[dict]:
        tasks = await self.service.get_linked_tasks(user_id, meeting_id)
        return [LinkedTaskResponse.model_validate(t) for t in tasks]

    async def get_linked_meetings(self, user_id: UUID, task_id: UUID) -> List[dict]:
        meetings = await self.service.get_linked_meetings(user_id, task_id)
        return [LinkedMeetingResponse.model_validate(m) for m in meetings]

    async def get_linked_tasks_for_session(self, user_id: UUID, session_id: UUID) -> List[dict]:
        tasks = await self.service.get_linked_tasks_for_session(user_id, session_id)
        return [LinkedTaskResponse.model_validate(t) for t in tasks]
