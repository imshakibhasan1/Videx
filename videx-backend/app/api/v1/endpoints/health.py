"""
Health Check Endpoint.

Used by load balancers, Docker health checks, and monitoring systems.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    service: str


@router.get("", response_model=HealthResponse, summary="Health Check")
async def health_check() -> HealthResponse:
    """Returns service health status. No auth required."""
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        service=settings.APP_NAME,
    )
