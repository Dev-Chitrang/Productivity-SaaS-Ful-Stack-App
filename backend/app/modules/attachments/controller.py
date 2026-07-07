from typing import Optional
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse

from app.modules.attachments.enums import AttachmentEntityType
from app.modules.attachments.exceptions import (
    AttachmentAccessDeniedException,
    AttachmentNotFoundException,
    AttachmentStorageError,
    AttachmentValidationError,
)
from app.modules.attachments.schemas import (
    AttachmentListResponse,
    AttachmentResponse,
    PresignedUploadResponse,
)
from app.modules.attachments.service import AttachmentService


class AttachmentController:
    def __init__(self, service: AttachmentService):
        self.service = service

    async def upload(
        self,
        owner_user_id: UUID,
        entity_type: AttachmentEntityType,
        entity_id: UUID,
        file: UploadFile,
    ) -> AttachmentResponse:
        try:
            attachment = await self.service.upload(
                owner_user_id=owner_user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                file=file,
            )
            return AttachmentResponse.model_validate(attachment)
        except AttachmentValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )
        except AttachmentStorageError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            )

    async def get_metadata(
        self, attachment_id: UUID, owner_user_id: UUID
    ) -> AttachmentResponse:
        try:
            attachment = await self.service.get_metadata(attachment_id, owner_user_id)
            return AttachmentResponse.model_validate(attachment)
        except AttachmentNotFoundException as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except AttachmentAccessDeniedException as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    async def download(
        self, attachment_id: UUID, owner_user_id: UUID
    ):
        try:
            result = await self.service.get_download_response(attachment_id, owner_user_id)
            if result["url"]:
                return RedirectResponse(url=result["url"])
            return FileResponse(
                path=result["path"],
                media_type=result["content_type"],
                filename=result["original_filename"],
            )
        except AttachmentNotFoundException as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except AttachmentAccessDeniedException as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    async def create_presigned_upload(
        self,
        owner_user_id: UUID,
        entity_type: AttachmentEntityType,
        entity_id: UUID,
        filename: str,
        content_type: str,
    ) -> PresignedUploadResponse:
        try:
            result = await self.service.create_presigned_upload(
                owner_user_id=owner_user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                filename=filename,
                content_type=content_type,
            )
            return PresignedUploadResponse(**result)
        except AttachmentStorageError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            )

    async def confirm_presigned_upload(
        self,
        owner_user_id: UUID,
        entity_type: AttachmentEntityType,
        entity_id: UUID,
        key: str,
        original_filename: str,
        content_type: str,
        size: int,
    ) -> AttachmentResponse:
        try:
            attachment = await self.service.confirm_presigned_upload(
                owner_user_id=owner_user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                key=key,
                original_filename=original_filename,
                content_type=content_type,
                size=size,
            )
            return AttachmentResponse.model_validate(attachment)
        except AttachmentStorageError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            )

    async def list_for_entity(
        self,
        entity_type: AttachmentEntityType,
        entity_id: UUID,
        owner_user_id: UUID,
    ) -> AttachmentListResponse:
        try:
            attachments = await self.service.list_for_entity(
                entity_type=entity_type,
                entity_id=entity_id,
                owner_user_id=owner_user_id,
            )
            return AttachmentListResponse(
                attachments=[AttachmentResponse.model_validate(a) for a in attachments],
                total_count=len(attachments),
            )
        except AttachmentAccessDeniedException as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    async def list_recent(
        self, owner_user_id: UUID, limit: int = 10
    ) -> AttachmentListResponse:
        attachments = await self.service.list_recent_for_user(owner_user_id, limit)
        return AttachmentListResponse(
            attachments=[AttachmentResponse.model_validate(a) for a in attachments],
            total_count=len(attachments),
        )

    async def delete(
        self, attachment_id: UUID, owner_user_id: UUID
    ) -> dict:
        try:
            await self.service.delete(attachment_id, owner_user_id)
            return {"status": "success", "message": "Attachment deleted successfully."}
        except AttachmentNotFoundException as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except AttachmentAccessDeniedException as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
