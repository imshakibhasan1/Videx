"""
VIDEX Job & AnalysisResult ORM Models.

Job: Tracks the full lifecycle of a video processing request.
AnalysisResult: Stores the Step 1 MiMo V2.5 analysis output.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.prompt import PromptConfig


class Job(UUIDPKMixin, TimestampMixin, Base):
    """
    Central tracking entity for every video processing pipeline run.

    Status lifecycle:
        queued → processing → analysis_done → generating_prompt → prompt_done
                                                                 ↘ failed (any stage)
    """

    __tablename__ = "jobs"

    # ── Foreign Keys ──────────────────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Status ────────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="queued",
        index=True,
        comment="queued|processing|analysis_done|generating_prompt|prompt_done|failed",
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ── Cloudinary ────────────────────────────────────────────────────────────
    cloudinary_url: Mapped[str] = mapped_column(Text, nullable=False)
    cloudinary_public_id: Mapped[str] = mapped_column(String(255), nullable=False)
    cloudinary_secure_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Video Metadata (populated post-upload) ────────────────────────────────
    video_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    video_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    video_format: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # ── Denormalized Analysis Result (JSONB for fast access) ──────────────────
    analysis_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    analysis_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="jobs")
    analysis: Mapped["AnalysisResult | None"] = relationship(
        "AnalysisResult",
        back_populates="job",
        uselist=False,
        cascade="all, delete-orphan",
    )
    prompt_configs: Mapped[list["PromptConfig"]] = relationship(
        "PromptConfig",
        back_populates="job",
        cascade="all, delete-orphan",
    )

    @property
    def is_analysis_ready(self) -> bool:
        return self.status in {"analysis_done", "generating_prompt", "prompt_done"}

    def __repr__(self) -> str:
        return f"<Job id={self.id} status={self.status!r} user_id={self.user_id}>"


class AnalysisResult(UUIDPKMixin, Base):
    """
    Normalized storage of MiMo V2.5 Step 1 analysis output.
    One-to-one with Job.
    """

    __tablename__ = "analysis_results"

    # ── Foreign Key ───────────────────────────────────────────────────────────
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # ── Core Fields ───────────────────────────────────────────────────────────
    scene_summary: Mapped[str] = mapped_column(Text, nullable=False)
    physical_properties: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    style_options: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    physics_flags: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    technical_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    raw_mimo_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    job: Mapped["Job"] = relationship("Job", back_populates="analysis")

    def __repr__(self) -> str:
        return f"<AnalysisResult id={self.id} job_id={self.job_id} confidence={self.confidence_score:.2f}>"
