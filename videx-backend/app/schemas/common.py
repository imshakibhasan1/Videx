"""
Shared/common Pydantic schema components.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseResponse(BaseModel):
    """Base for all API response schemas."""
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseResponse):
    """Simple success acknowledgement."""
    message: str


class ErrorResponse(BaseResponse):
    """Standard error envelope."""
    error: str
    message: str
    detail: str | None = None


class PaginationMeta(BaseResponse):
    total: int
    page: int
    per_page: int
    total_pages: int


class JobStatusResponse(BaseResponse):
    job_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
