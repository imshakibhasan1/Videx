"""
Upload Pydantic Schemas.
Covers: Cloudinary signature request/response and job creation.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import BaseResponse


class SignatureRequest(BaseModel):
    """Request body for POST /upload/signature."""
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., description="MIME type, e.g. video/mp4")

    @property
    def is_valid_video_mime(self) -> bool:
        allowed = {"video/mp4", "video/quicktime", "video/webm", "video/x-msvideo", "video/avi"}
        return self.content_type.lower() in allowed


class SignatureResponse(BaseResponse):
    """
    Response body for POST /upload/signature.
    The frontend uses these values to upload directly to Cloudinary.
    """
    signature: str
    timestamp: int
    api_key: str
    cloud_name: str
    folder: str
    upload_url: str  # Full Cloudinary upload endpoint URL
    public_id: str   # Pre-assigned Cloudinary public ID
    job_id: UUID     # Pre-created job record for tracking


class UploadConfirmRequest(BaseModel):
    """
    Request body for POST /upload/confirm.
    Called after a successful direct Cloudinary upload to finalize the job.
    """
    job_id: UUID
    cloudinary_public_id: str
    cloudinary_secure_url: str
    video_duration: float = Field(..., ge=0, le=15, description="Duration in seconds (max 15s)")
    video_size_bytes: int = Field(..., ge=1, le=52_428_800, description="File size (max 50MB)")
    video_format: str = Field(..., max_length=20)


class UploadConfirmResponse(BaseResponse):
    job_id: UUID
    status: str = "queued"
    message: str = "Video upload confirmed. Analysis has been queued."
    celery_task_id: str | None = None
