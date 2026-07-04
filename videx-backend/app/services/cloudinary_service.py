"""
Cloudinary Service.

Responsibilities:
- Generate signed upload parameters for direct client-to-CDN uploads
- Validate uploaded video metadata (size, duration)
- Delete temporary uploads on job failure/expiry
- Never touches actual video bytes (no server-side bandwidth waste)
"""

from __future__ import annotations

import logging
import time
import uuid

import cloudinary
import cloudinary.utils

from app.config import settings
from app.core.exceptions import CloudinaryError, UploadError

logger = logging.getLogger(__name__)

# ── Configure SDK once at module load ─────────────────────────────────────────
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)

ALLOWED_MIME_TYPES = frozenset({
    "video/mp4",
    "video/quicktime",
    "video/webm",
    "video/x-msvideo",
    "video/avi",
    "video/mov",
})


class CloudinaryService:
    """Stateless service — all methods are static or class methods."""

    @classmethod
    def generate_upload_signature(
        cls,
        job_id: uuid.UUID,
        content_type: str,
    ) -> dict[str, str | int]:
        """
        Generate a signed set of parameters for a direct browser→Cloudinary upload.

        The secret stays server-side; the frontend receives only the signature,
        timestamp, api_key, and upload URL.

        Returns a dict with: signature, timestamp, api_key, cloud_name, folder,
                             upload_url, public_id.
        """
        if content_type.lower() not in ALLOWED_MIME_TYPES:
            raise UploadError(
                f"Unsupported video format: {content_type}.",
                detail=f"Allowed types: {sorted(ALLOWED_MIME_TYPES)}",
            )

        timestamp = int(time.time())
        # public_id should NOT include the folder prefix — Cloudinary will place it
        # in the folder automatically. Including folder in both public_id and params
        # causes signature mismatch (401).
        public_id = f"job_{job_id}"
        folder = settings.CLOUDINARY_FOLDER

        # Only include params that Cloudinary will verify during upload.
        # Do NOT include resource_type or invalidate — they are not part of
        # the upload signature verification.
        params_to_sign = {
            "timestamp": timestamp,
            "public_id": public_id,
            "folder": folder,
        }

        try:
            signature = cloudinary.utils.api_sign_request(
                params_to_sign,
                settings.CLOUDINARY_API_SECRET,
            )
        except Exception as exc:
            logger.exception("Cloudinary signature generation failed")
            raise CloudinaryError(detail=str(exc)) from exc

        upload_url = (
            f"https://api.cloudinary.com/v1_1/{settings.CLOUDINARY_CLOUD_NAME}/video/upload"
        )

        return {
            "signature": signature,
            "timestamp": timestamp,
            "api_key": settings.CLOUDINARY_API_KEY,
            "cloud_name": settings.CLOUDINARY_CLOUD_NAME,
            "folder": folder,
            "upload_url": upload_url,
            "public_id": public_id,
        }

    @classmethod
    def validate_upload_metadata(
        cls,
        duration_seconds: float,
        size_bytes: int,
    ) -> None:
        """
        Enforce server-side size and duration limits.
        Raises UploadError if limits are exceeded.
        """
        if size_bytes > settings.CLOUDINARY_MAX_BYTES:
            max_mb = settings.CLOUDINARY_MAX_BYTES // (1024 * 1024)
            raise UploadError(
                f"Video file exceeds the {max_mb}MB size limit.",
                detail=f"Uploaded: {size_bytes / (1024 * 1024):.1f}MB",
            )

        if duration_seconds > settings.CLOUDINARY_MAX_DURATION:
            raise UploadError(
                f"Video duration exceeds the {settings.CLOUDINARY_MAX_DURATION}s limit.",
                detail=f"Uploaded duration: {duration_seconds:.1f}s",
            )

    @classmethod
    def build_secure_url(cls, public_id: str) -> str:
        """Build a secure (HTTPS) Cloudinary URL for a given public ID."""
        url, _ = cloudinary.utils.cloudinary_url(
            public_id,
            resource_type="video",
            secure=True,
        )
        return url

    @classmethod
    async def delete_asset(cls, public_id: str) -> None:
        """
        Delete a Cloudinary asset. Called on job failure or expiry cleanup.
        Uses the Admin API (server-to-server).
        """
        import cloudinary.api  # noqa: PLC0415

        try:
            cloudinary.api.delete_resources([public_id], resource_type="video", invalidate=True)
            logger.info("Cloudinary asset deleted: %s", public_id)
        except Exception as exc:
            # Non-fatal: log but don't raise (cleanup failure shouldn't block user)
            logger.warning("Failed to delete Cloudinary asset %s: %s", public_id, exc)
