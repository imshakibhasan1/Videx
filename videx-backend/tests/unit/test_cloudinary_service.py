"""Unit tests for Cloudinary Service."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest

from app.core.exceptions import CloudinaryError, UploadError
from app.services.cloudinary_service import CloudinaryService


def test_generate_signature_valid():
    """Signature is generated for valid video MIME type."""
    job_id = uuid.uuid4()
    with patch("cloudinary.utils.api_sign_request", return_value="test_signature"):
        result = CloudinaryService.generate_upload_signature(job_id, "video/mp4")

    assert result["signature"] == "test_signature"
    assert result["cloud_name"] is not None
    assert str(job_id) in str(result["public_id"])


def test_generate_signature_invalid_mime():
    """Raises UploadError for non-video MIME types."""
    with pytest.raises(UploadError, match="Unsupported video format"):
        CloudinaryService.generate_upload_signature(uuid.uuid4(), "image/jpeg")


def test_validate_upload_metadata_size_limit():
    """Raises UploadError when file exceeds 50MB."""
    with pytest.raises(UploadError, match="size limit"):
        CloudinaryService.validate_upload_metadata(
            duration_seconds=10.0,
            size_bytes=60 * 1024 * 1024,  # 60MB
        )


def test_validate_upload_metadata_duration_limit():
    """Raises UploadError when duration exceeds 15 seconds."""
    with pytest.raises(UploadError, match="duration"):
        CloudinaryService.validate_upload_metadata(
            duration_seconds=20.0,
            size_bytes=10 * 1024 * 1024,
        )


def test_validate_upload_metadata_valid():
    """No exception raised for valid upload metadata."""
    CloudinaryService.validate_upload_metadata(
        duration_seconds=12.0,
        size_bytes=30 * 1024 * 1024,  # 30MB — within limits
    )
