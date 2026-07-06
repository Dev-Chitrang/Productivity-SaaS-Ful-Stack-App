from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
from app.modules.entity_links.enums import RelationOrigin, EntityType


class EntityLinkCreate(BaseModel):
    source_type: EntityType
    source_id: UUID
    target_type: EntityType
    target_id: UUID
    link_type: str = "RELATED_TO"
    relation_origin: RelationOrigin = RelationOrigin.USER


class EntityLinkResponse(BaseModel):
    id: UUID
    source_type: str
    source_id: UUID
    target_type: str
    target_id: UUID
    link_type: str
    relation_origin: RelationOrigin
    created_by: UUID
    created_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EntityLinkListResponse(BaseModel):
    links: List[EntityLinkResponse]
    total_count: int


class LinkedTaskResponse(BaseModel):
    id: UUID
    title: str
    priority: str
    status: str
    due_date: Optional[datetime] = None
    link_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class LinkedMeetingResponse(BaseModel):
    id: UUID
    title: str
    status: str
    meeting_code: str
    scheduled_start: Optional[datetime] = None
    link_id: Optional[UUID] = None
    session_id: Optional[UUID] = None

    class Config:
        from_attributes = True
