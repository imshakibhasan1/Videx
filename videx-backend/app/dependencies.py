"""
VIDEX Dependency Injection.

Provides reusable FastAPI dependencies for:
- Async database sessions
- Current authenticated user extraction (from JWT)
- Optional user (for public routes)
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.models.user import User

# ── HTTP Bearer scheme ────────────────────────────────────────────────────────
bearer_scheme = HTTPBearer(auto_error=False)


# ── Database ──────────────────────────────────────────────────────────────────
async def get_db() -> AsyncSession:  # type: ignore[return]
    """Yield an async SQLAlchemy session, always closing on exit."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


DbSession = Annotated[AsyncSession, Depends(get_db)]


# ── Token extraction ──────────────────────────────────────────────────────────
def _extract_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str:
    """
    Extract a raw JWT string using a two-channel fallback strategy:

    1. ``Authorization: Bearer <token>`` header  (standard REST clients)
    2. ``?token=<token>`` URL query parameter     (SSE / EventSource — browsers
       cannot send custom headers with the native EventSource API)

    Raises AuthenticationError if neither channel provides a token.
    """
    # Channel 1: Authorization header (preferred)
    if credentials is not None and credentials.credentials:
        return credentials.credentials

    # Channel 2: ?token= query param (SSE fallback)
    token_param: str | None = request.query_params.get("token")
    if token_param:
        return token_param

    raise AuthenticationError("Missing authentication token.")


# ── Authentication ────────────────────────────────────────────────────────────
async def get_current_user(
    request: Request,
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> User:
    """
    Extract and validate the current user from the Bearer token.

    Accepts the JWT via:
    - ``Authorization: Bearer <token>`` header (standard)
    - ``?token=<token>`` query parameter       (SSE / EventSource fallback)

    Raises AuthenticationError (401) if token is missing, invalid, or user not found.
    """
    from sqlalchemy import select  # noqa: PLC0415

    raw_token = _extract_token(request, credentials)

    try:
        payload = decode_token(raw_token)
    except ValueError as exc:
        raise AuthenticationError(detail=str(exc)) from exc

    if payload.get("type") != "access":
        raise AuthenticationError("Invalid token type. Expected access token.")

    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise AuthenticationError("Token subject is missing.")

    try:
        user_id = UUID(user_id_str)
    except ValueError as exc:
        raise AuthenticationError("Token subject is not a valid UUID.") from exc

    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user: User | None = result.scalar_one_or_none()

    if user is None:
        raise AuthenticationError("User account not found or deactivated.")

    return user


async def get_current_user_optional(
    request: Request,
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> User | None:
    """Return the current user or None (for routes that support anonymous access)."""
    if credentials is None and not request.query_params.get("token"):
        return None
    try:
        return await get_current_user(request, db, credentials)
    except (AuthenticationError, HTTPException):
        return None


# ── Typed aliases for endpoint signatures ────────────────────────────────────
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
