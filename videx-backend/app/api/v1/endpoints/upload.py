"""
Upload Endpoints.

POST /upload/signature — Generate a Cloudinary signed upload URL
POST /upload/confirm   — Confirm upload completed and queue analysis
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, status

from app.config import settings
from app.core.exceptions import UploadError
from app.dependencies import CurrentUser, DbSession
from app.models.job import Job
from app.schemas.upload import (
    SignatureRequest,
    SignatureResponse,
    UploadConfirmRequest,
    UploadConfirmResponse,
)
from app.services.cloudinary_service import CloudinaryService
from app.tasks.analyze_task import run_video_analysis

router = APIRouter()


@router.post(
    "/signature",
    response_model=SignatureResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Cloudinary signed upload parameters",
)
async def get_upload_signature(
    body: SignatureRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> SignatureResponse:
    """
    Step 1a — Generate a server-signed upload token for direct browser→Cloudinary upload.

    The frontend uses the returned signature + api_key + timestamp to upload
    the video file directly to Cloudinary without routing through this server.
    A Job record is pre-created to track the upload lifecycle.
    """
    # Validate MIME type early
    if not body.is_valid_video_mime:
        raise UploadError(
            f"Unsupported file type: {body.content_type}.",
            detail="Accepted: video/mp4, video/quicktime, video/webm, video/avi",
        )

    # Pre-create the Job record
    job_id = uuid.uuid4()
    job = Job(
        id=job_id,
        user_id=current_user.id,
        status="queued",
        cloudinary_url="",       # Will be filled after upload confirmation
        cloudinary_public_id="", # Will be filled after upload confirmation
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(job)
    await db.flush()

    # Generate Cloudinary signature
    sig_data = CloudinaryService.generate_upload_signature(job_id, body.content_type)

    return SignatureResponse(
        signature=str(sig_data["signature"]),
        timestamp=int(sig_data["timestamp"]),
        api_key=str(sig_data["api_key"]),
        cloud_name=str(sig_data["cloud_name"]),
        folder=str(sig_data["folder"]),
        upload_url=str(sig_data["upload_url"]),
        public_id=str(sig_data["public_id"]),
        job_id=job_id,
    )


@router.post(
    "/confirm",
    response_model=UploadConfirmResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm upload and trigger analysis",
)
async def confirm_upload(
    body: UploadConfirmRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> UploadConfirmResponse:
    """
    Step 1b — Called after the frontend successfully uploads to Cloudinary.

    Validates size/duration constraints, updates the Job record,
    and dispatches the async analysis Celery task.
    """
    from sqlalchemy import select  # noqa: PLC0415

    from app.models.job import Job as JobModel  # noqa: PLC0415

    # Fetch and verify job ownership
    result = await db.execute(
        select(JobModel).where(
            JobModel.id == body.job_id,
            JobModel.user_id == current_user.id,
        )
    )
    job: Job | None = result.scalar_one_or_none()
    if job is None:
        raise UploadError("Job not found or does not belong to your account.")

    # Server-side validation of upload metadata
    CloudinaryService.validate_upload_metadata(
        duration_seconds=body.video_duration,
        size_bytes=body.video_size_bytes,
    )

    # Update job with Cloudinary asset info
    job.cloudinary_url = body.cloudinary_secure_url
    job.cloudinary_secure_url = body.cloudinary_secure_url
    job.cloudinary_public_id = body.cloudinary_public_id
    job.video_duration_seconds = int(body.video_duration)
    job.video_size_bytes = body.video_size_bytes
    job.video_format = body.video_format
    job.status = "queued"
    job.updated_at = datetime.now(timezone.utc)
    await db.flush()

    # Dispatch async analysis task
    celery_task = run_video_analysis.apply_async(
        args=[str(body.job_id), str(current_user.id)],
        queue="analysis",
    )
    job.celery_task_id = celery_task.id
    await db.flush()

    return UploadConfirmResponse(
        job_id=body.job_id,
        status="queued",
        message="Video confirmed. Analysis has been queued.",
        celery_task_id=celery_task.id,
    )
