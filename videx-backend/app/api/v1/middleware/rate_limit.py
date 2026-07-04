"""
VIDEX Rate Limiting Middleware.

Uses slowapi (which wraps limits) to rate limit requests based on IP or User ID.
Currently configured for Free Tier MVP limits.
"""

from __future__ import annotations

from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings

def get_user_identifier(request: Request) -> str:
    """
    Identify user by X-User-ID header if available (from auth layer),
    otherwise fallback to IP address.
    """
    if "X-User-ID" in request.headers:
        return request.headers["X-User-ID"]
    return get_remote_address(request)

# Global limiter instance
limiter = Limiter(key_func=get_user_identifier)

# Rate limit strings based on settings
UPLOAD_LIMIT = f"{settings.RATE_LIMIT_UPLOADS_PER_HOUR}/hour"
PROMPT_LIMIT = f"{settings.RATE_LIMIT_PROMPTS_PER_DAY}/day"

def setup_rate_limiting(app):
    """Register the slowapi exception handler on the FastAPI app."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
