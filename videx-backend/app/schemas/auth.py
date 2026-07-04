"""
Auth Pydantic Schemas.
Covers: Registration, Login, Token responses.
"""

from __future__ import annotations

import re
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.common import BaseResponse

_PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&_\-#])[A-Za-z\d@$!%*?&_\-#]{8,128}$"
)


class RegisterRequest(BaseModel):
    """Request body for POST /auth/register."""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not _PASSWORD_PATTERN.match(v):
            raise ValueError(
                "Password must be 8–128 characters and contain at least one uppercase letter, "
                "one lowercase letter, one digit, and one special character (@$!%*?&_-#)."
            )
        return v


class LoginRequest(BaseModel):
    """Request body for POST /auth/login."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseResponse):
    """Response body for successful authentication."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Access token TTL in seconds


class RefreshRequest(BaseModel):
    """Request body for POST /auth/refresh."""
    refresh_token: str


class UserResponse(BaseResponse):
    """Public user profile."""
    id: UUID
    email: str
    name: str | None
    avatar_url: str | None
    provider: str
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)
