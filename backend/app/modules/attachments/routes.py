from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.modules.attachments.controller import AttachmentController
from app.modules.attachments.dependencies import (
    get_attachment_service,
    get_current_user_id,
)
from app.modules.attachments.enums import AttachmentEntityType
from app.modules.attachments.schemas import (
    AttachmentListResponse,
    AttachmentResponse,
    ConfirmUploadRequest,
    PresignedUploadRequest,
    PresignedUploadResponse,
)
from app.modules.attachments.service import AttachmentService

from app.core.rate_limit import RateLimiter

router = APIRouter(
    prefix="/attachments",
    tags=["Generic Attachment Infrastructure"],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=AttachmentResponse,
    summary="Upload a file attachment for any supported entity",
    dependencies=[Depends(RateLimiter(3, 60, "file_upload"))],
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


@router.post(
    "/presigned-upload",
    status_code=status.HTTP_200_OK,
    response_model=PresignedUploadResponse,
    summary="Generate a presigned URL for direct-to-S3 upload",
    dependencies=[Depends(RateLimiter(10, 60, "file_upload"))],
)
async def create_presigned_upload_endpoint(
    payload: PresignedUploadRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    service: AttachmentService = Depends(get_attachment_service),
):
    ctrl = AttachmentController(service)
    return await ctrl.create_presigned_upload(
        owner_user_id=current_user_id,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        filename=payload.filename,
        content_type=payload.content_type,
    )


@router.post(
    "/confirm-upload",
    status_code=status.HTTP_201_CREATED,
    response_model=AttachmentResponse,
    summary="Confirm a direct-to-S3 upload and store metadata",
    dependencies=[Depends(RateLimiter(10, 60, "file_upload"))],
)
async def confirm_upload_endpoint(
    payload: ConfirmUploadRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    service: AttachmentService = Depends(get_attachment_service),
):
    ctrl = AttachmentController(service)
    return await ctrl.confirm_presigned_upload(
        owner_user_id=current_user_id,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        key=payload.key,
        original_filename=payload.original_filename,
        content_type=payload.content_type,
        size=payload.size,
    )


@router.get(
    "/recent",
    status_code=status.HTTP_200_OK,
    response_model=AttachmentListResponse,
    summary="List the most recent attachments for the current user",
    dependencies=[Depends(RateLimiter(60, 60, "general_get"))],
)
async def list_recent_attachments_endpoint(
    limit: int = Query(10, ge=1, le=50),
    current_user_id: UUID = Depends(get_current_user_id),
    service: AttachmentService = Depends(get_attachment_service),
):
    ctrl = AttachmentController(service)
    return await ctrl.list_recent(current_user_id, limit)


@router.get(
    "/{attachment_id}",
    status_code=status.HTTP_200_OK,
    response_model=AttachmentResponse,
    summary="Retrieve attachment metadata",
    dependencies=[Depends(RateLimiter(60, 60, "general_get"))],
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
    summary="Download an attachment file (redirects to presigned URL for S3)",
    dependencies=[Depends(RateLimiter(60, 60, "general_get"))],
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
    dependencies=[Depends(RateLimiter(20, 60, "write_entity"))],
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
    dependencies=[Depends(RateLimiter(60, 60, "general_get"))],
)
async def list_entity_attachments_endpoint(
    entity_type: AttachmentEntityType,
    entity_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    service: AttachmentService = Depends(get_attachment_service),
):
    ctrl = AttachmentController(service)
    return await ctrl.list_for_entity(entity_type, entity_id, current_user_id)
