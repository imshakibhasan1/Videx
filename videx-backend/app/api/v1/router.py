"""
VIDEX API v1 — Aggregated Router.

Registers all endpoint modules under a single /api/v1 prefix.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    analyze,
    auth,
    health,
    prompts,
    stream,
    upload,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(upload.router, prefix="/upload", tags=["Upload"])
api_router.include_router(analyze.router, prefix="/analyze", tags=["Analysis"])
api_router.include_router(prompts.router, prefix="/prompts", tags=["Prompts"])
api_router.include_router(stream.router, prefix="/stream", tags=["SSE Stream"])
