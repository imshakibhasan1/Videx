"""
VIDEX Security Utilities.

Handles:
- Password hashing (bcrypt — direct, bypassing passlib which is broken with bcrypt 5.x)
- JWT access and refresh token creation
- Token decoding and validation
- Share token generation (for public prompt sharing)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.config import settings

# ── Password hashing ──────────────────────────────────────────────────────────
# Using bcrypt directly — passlib 1.7.4 is incompatible with bcrypt 5.x and
# crashes during its own internal self-test (detect_wrap_bug). bcrypt is already
# installed as a transitive dependency and works correctly on its own.
_BCRYPT_ROUNDS = 12


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Constant-time bcrypt verification."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Hash a plaintext password with bcrypt (cost factor 12)."""
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


# ── JWT helpers ───────────────────────────────────────────────────────────────
def _build_payload(subject: str, token_type: str, expire: datetime) -> dict[str, Any]:
    return {
        "sub": subject,
        "type": token_type,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),  # Unique token ID for future revocation support
    }


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """
    Create a short-lived JWT access token.
    Default expiry: ACCESS_TOKEN_EXPIRE_MINUTES from settings.
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = _build_payload(str(subject), "access", expire)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str | Any) -> str:
    """
    Create a long-lived JWT refresh token.
    Default expiry: REFRESH_TOKEN_EXPIRE_DAYS from settings.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = _build_payload(str(subject), "refresh", expire)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.
    Raises ValueError with a human-readable message on any failure.
    """
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise ValueError(f"Token validation failed: {exc}") from exc


# ── Share tokens ──────────────────────────────────────────────────────────────
def generate_share_token() -> str:
    """
    Generate a cryptographically random 48-char hex share token.
    Used as the public slug for shareable prompts.
    """
    return uuid.uuid4().hex + uuid.uuid4().hex[:16]
