"""
Authentication Endpoints.

POST /auth/register  — Create a new account (email + password)
POST /auth/login     — Get access + refresh tokens
POST /auth/refresh   — Rotate tokens using refresh token
GET  /auth/me        — Get current user profile
"""

from __future__ import annotations

from fastapi import APIRouter, status
from sqlalchemy import select

from app.config import settings
from app.core.exceptions import AuthenticationError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.dependencies import CurrentUser, DbSession
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.common import MessageResponse

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(body: RegisterRequest, db: DbSession) -> TokenResponse:
    """
    Create a new VIDEX account.
    Returns access + refresh tokens on success.
    """
    # Check for existing account
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise ValidationError(
            "An account with this email already exists.",
            detail="Please log in or use a different email address.",
        )

    user = User(
        email=body.email,
        name=body.name,
        hashed_password=get_password_hash(body.password),
        provider="email",
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/login", response_model=TokenResponse, summary="Authenticate and get tokens")
async def login(body: LoginRequest, db: DbSession) -> TokenResponse:
    """Authenticate with email + password. Returns JWT access + refresh tokens."""
    result = await db.execute(
        select(User).where(User.email == body.email, User.is_active.is_(True))
    )
    user: User | None = result.scalar_one_or_none()

    if user is None or user.hashed_password is None:
        raise AuthenticationError("Invalid email or password.")

    if not verify_password(body.password, user.hashed_password):
        raise AuthenticationError("Invalid email or password.")

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse, summary="Rotate access token")
async def refresh_token(body: RefreshRequest, db: DbSession) -> TokenResponse:
    """
    Exchange a valid refresh token for a new access + refresh token pair.
    Implements token rotation for enhanced security.
    """
    try:
        payload = decode_token(body.refresh_token)
    except ValueError as exc:
        raise AuthenticationError("Invalid refresh token.", detail=str(exc)) from exc

    if payload.get("type") != "refresh":
        raise AuthenticationError("Invalid token type. Expected a refresh token.")

    user_id: str = payload.get("sub", "")
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active.is_(True))
    )
    user: User | None = result.scalar_one_or_none()
    if user is None:
        raise AuthenticationError("User not found or deactivated.")

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse, summary="Get current user profile")
async def get_me(current_user: CurrentUser) -> UserResponse:
    """Return the authenticated user's profile. Requires valid access token."""
    return UserResponse.model_validate(current_user)
