"""
VIDEX PromptConfig & GeneratedPrompt ORM Models.

PromptConfig: Stores user-selected rendering parameters (Step 2).
GeneratedPrompt: Stores the final Detractor Engine output (Step 3).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.job import Job


class PromptConfig(UUIDPKMixin, Base):
    """User-chosen rendering parameters for the Detractor Engine."""

    __tablename__ = "prompt_configs"

    # ── Foreign Keys ──────────────────────────────────────────────────────────
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_results.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── User-Selected Parameters ──────────────────────────────────────────────
    selected_style: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="original",
        comment="original|cinematic|documentary",
    )
    duration: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="8s",
        comment="8s|10s|15s",
    )
    aspect_ratio: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="16:9",
        comment="16:9|9:16|1:1",
    )
    frame_rate: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    custom_overrides: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    job: Mapped["Job"] = relationship("Job", back_populates="prompt_configs")
    generated_prompt: Mapped["GeneratedPrompt | None"] = relationship(
        "GeneratedPrompt",
        back_populates="config",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<PromptConfig id={self.id} style={self.selected_style!r} "
            f"duration={self.duration!r} ratio={self.aspect_ratio!r}>"
        )


class GeneratedPrompt(UUIDPKMixin, Base):
    """Final Detractor Engine output — the production-ready T2V prompt."""

    __tablename__ = "generated_prompts"

    # ── Foreign Keys ──────────────────────────────────────────────────────────
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompt_configs.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Prompt Content ────────────────────────────────────────────────────────
    final_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    raw_mimo_response: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Quality Scores ────────────────────────────────────────────────────────
    physics_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # ── Sharing ───────────────────────────────────────────────────────────────
    share_token: Mapped[str | None] = mapped_column(
        String(64),
        unique=True,
        nullable=True,
        index=True,
        comment="48-char hex token for public sharing",
    )
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    copy_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    config: Mapped["PromptConfig"] = relationship("PromptConfig", back_populates="generated_prompt")

    def __repr__(self) -> str:
        return (
            f"<GeneratedPrompt id={self.id} physics={self.physics_score:.2f} "
            f"quality={self.quality_score:.2f} public={self.is_public}>"
        )
