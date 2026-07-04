"""
Analysis Service — Step 1 Orchestrator.

Coordinates the full video analysis pipeline:
1. Validates job ownership
2. Marks job as 'processing'
3. Calls MiMo V2.5 with the Cloudinary video URL
4. Persists the AnalysisResult to PostgreSQL
5. Updates Job status and JSONB cache
6. Publishes SSE event via Redis
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AnalysisError, AuthorizationError, NotFoundError
from app.models.job import AnalysisResult, Job
from app.schemas.analysis import AnalysisResultResponse, MiMoAnalysisPayload
from app.services.mimo_service import mimo_service
from app.services.sse_service import SSEService

logger = logging.getLogger(__name__)


class AnalysisService:

    @staticmethod
    async def get_job_or_404(db: AsyncSession, job_id: UUID, user_id: UUID) -> Job:
        """Fetch a job and enforce ownership."""
        result = await db.execute(select(Job).where(Job.id == job_id))
        job: Job | None = result.scalar_one_or_none()

        if job is None:
            raise NotFoundError("Job", str(job_id))
        if job.user_id != user_id:
            raise AuthorizationError("You do not own this job.")
        return job

    @staticmethod
    async def run_analysis(db: AsyncSession, job_id: UUID, user_id: UUID) -> None:
        """
        Full analysis pipeline executed inside a Celery task.

        Designed to be idempotent: safe to retry if interrupted.
        """
        job = await AnalysisService.get_job_or_404(db, job_id, user_id)

        # ── Guard: don't re-analyze a completed job ───────────────────────────
        if job.status in {"analysis_done", "prompt_done"}:
            logger.info("Job %s already analyzed — skipping.", job_id)
            return

        # ── 1. Mark as processing ─────────────────────────────────────────────
        job.status = "processing"
        await db.flush()
        await SSEService.publish(str(job_id), {"event": "analysis_started", "job_id": str(job_id)})

        # ── 2. Call MiMo V2.5 ─────────────────────────────────────────────────
        logger.info("Starting MiMo V2.5 analysis for job %s", job_id)
        try:
            analysis: MiMoAnalysisPayload = await mimo_service.analyze_video(
                video_url=job.cloudinary_secure_url or job.cloudinary_url
            )
        except Exception as exc:
            # Mark job as failed and propagate
            job.status = "failed"
            job.error_message = str(exc)
            await db.flush()
            await SSEService.publish(
                str(job_id),
                {"event": "analysis_failed", "job_id": str(job_id), "error": str(exc)},
            )
            raise AnalysisError(detail=str(exc)) from exc

        # ── 3. Persist AnalysisResult ─────────────────────────────────────────
        now = datetime.now(timezone.utc)
        analysis_record = AnalysisResult(
            job_id=job_id,
            scene_summary=analysis.scene_summary,
            physical_properties=analysis.physical_properties.model_dump(),
            style_options=[opt.model_dump() for opt in analysis.style_options],
            physics_flags=analysis.physics_flags.model_dump(),
            technical_metadata=analysis.technical_metadata.model_dump(),
            confidence_score=analysis.confidence_score,
            created_at=now,
        )
        db.add(analysis_record)

        # ── 4. Update Job with denormalized cache ─────────────────────────────
        job.status = "analysis_done"
        job.analysis_result = analysis.model_dump()
        job.analysis_completed_at = now
        await db.flush()

        # ── 5. Publish SSE completion event ───────────────────────────────────
        await db.refresh(analysis_record)
        await SSEService.publish(
            str(job_id),
            {
                "event": "analysis_complete",
                "job_id": str(job_id),
                "analysis_id": str(analysis_record.id),
                "confidence_score": analysis.confidence_score,
            },
        )
        logger.info(
            "Analysis complete for job %s (analysis_id=%s, confidence=%.2f)",
            job_id,
            analysis_record.id,
            analysis.confidence_score,
        )

    @staticmethod
    async def get_analysis_result(
        db: AsyncSession, job_id: UUID, user_id: UUID
    ) -> AnalysisResultResponse:
        """Retrieve a completed analysis result for API response."""
        job = await AnalysisService.get_job_or_404(db, job_id, user_id)

        result = await db.execute(select(AnalysisResult).where(AnalysisResult.job_id == job_id))
        ar = result.scalar_one_or_none()

        if ar is None:
            raise AnalysisError(
                f"Analysis for job {job_id} is not yet complete.",
                detail=f"Current status: {job.status}",
            )

        return AnalysisResultResponse(
            analysis_id=ar.id,
            job_id=job_id,
            scene_summary=ar.scene_summary,
            physical_properties=ar.physical_properties,
            style_options=ar.style_options,
            physics_flags=ar.physics_flags,
            technical_metadata=ar.technical_metadata,
            confidence_score=ar.confidence_score,
        )
