from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse

from app.modules.attachments.controller import AttachmentController
from app.modules.attachments.dependencies import (
    get_attachment_service,
    get_current_user_id,
)
from app.modules.attachments.enums import AttachmentEntityType
from app.modules.attachments.schemas import AttachmentListResponse, AttachmentResponse
from app.modules.attachments.service import AttachmentService

router = APIRouter(
    prefix="/attachments",
    tags=["Generic Attachment Infrastructure"],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=AttachmentResponse,
    summary="Upload a file attachment for any supported entity",
)
async def upload_attachment_endpoint(
    entity_type: AttachmentEntityType = Form(...),
    entity_id: UUID = Form(...),
    file: UploadFile = File(...),
    current_user_id: UUID = Depends(get_current_user_id),
    service: AttachmentService = Depends(get_attachment_service),
):
    ctrl = AttachmentController(service)
    return await ctrl.upload(
        owner_user_id=current_user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        file=file,
    )


@router.get(
    "/{attachment_id}",
    status_code=status.HTTP_200_OK,
    response_model=AttachmentResponse,
    summary="Retrieve attachment metadata",
)
async def get_attachment_metadata_endpoint(
    attachment_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: AttachmentService = Depends(get_attachment_service),
):
    ctrl = AttachmentController(service)
    return await ctrl.get_metadata(attachment_id, current_user_id)


@router.get(
    "/{attachment_id}/download",
    response_class=FileResponse,
    summary="Download an attachment file",
)
async def download_attachment_endpoint(
    attachment_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: AttachmentService = Depends(get_attachment_service),
):
    ctrl = AttachmentController(service)
    return await ctrl.download(attachment_id, current_user_id)


@router.delete(
    "/{attachment_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an attachment and its stored file",
)
async def delete_attachment_endpoint(
    attachment_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: AttachmentService = Depends(get_attachment_service),
):
    ctrl = AttachmentController(service)
    return await ctrl.delete(attachment_id, current_user_id)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=AttachmentListResponse,
    summary="List all attachments for a given entity",
)
async def list_entity_attachments_endpoint(
    entity_type: AttachmentEntityType,
    entity_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: AttachmentService = Depends(get_attachment_service),
):
    ctrl = AttachmentController(service)
    return await ctrl.list_for_entity(entity_type, entity_id, current_user_id)
