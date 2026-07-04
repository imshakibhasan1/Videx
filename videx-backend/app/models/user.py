"""
VIDEX User ORM Model.

Supports email/password registration (NextAuth credentials provider)
and OAuth providers (Google) via the provider/provider_id columns.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.job import Job


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    # ── Identity ──────────────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Auth Provider ─────────────────────────────────────────────────────────
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="email",
        comment="Auth provider: 'email' or 'google'",
    )
    provider_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="OAuth provider's user ID (for non-email providers)",
    )
    hashed_password: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="bcrypt hash — null for OAuth-only accounts",
    )

    # ── Status ────────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    jobs: Mapped[list["Job"]] = relationship(
        "Job",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
