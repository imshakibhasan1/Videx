"""
VIDEX FastAPI Application Factory.

Responsibilities:
- Creates the FastAPI app instance with lifespan management
- Registers all middleware (CORS, TrustedHost, request-ID injection)
- Mounts the versioned API router
- Registers global exception handlers
"""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.exceptions import VidexBaseException
from app.db.session import create_db_tables

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and graceful shutdown."""
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info("🚀 %s v%s starting up...", settings.APP_NAME, settings.APP_VERSION)
    await create_db_tables()
    logger.info("✅ Database tables verified/created")
    yield
    # ── Shutdown ─────────────────────────────────────────────────────────────
    logger.info("🛑 %s shutting down gracefully...", settings.APP_NAME)


def create_application() -> FastAPI:
    """Application factory — call once at module level."""
    # Late import to avoid circular dependency at module parse time
    from app.api.v1.router import api_router  # noqa: PLC0415

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-Powered Video Reverse-Engineering Platform",
        contact={"name": "VIDEX Engineering", "url": "https://videx.app"},
        license_info={"name": "Proprietary"},
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
        openapi_url="/api/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── Middleware stack (applied bottom-up) ─────────────────────────────────

    # 1. CORS — must be first outer layer
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    # 2. TrustedHost — production hardening
    if not settings.DEBUG:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["videx.app", "*.videx.app", "api.videx.app"],
        )

    # ── Request-ID injection ─────────────────────────────────────────────────
    @app.middleware("http")
    async def inject_request_id(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # ── Global exception handlers ─────────────────────────────────────────────
    @app.exception_handler(VidexBaseException)
    async def videx_exception_handler(request: Request, exc: VidexBaseException) -> JSONResponse:
        logger.warning(
            "VidexException [%s]: %s — %s",
            exc.error_code,
            exc.message,
            exc.detail,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url)
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again.",
                "detail": str(exc) if settings.DEBUG else None,
            },
        )

    # ── Routers ──────────────────────────────────────────────────────────────
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_application()
