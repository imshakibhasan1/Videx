"""
Prompt Service — Step 3 Detractor Engine Orchestrator.

Coordinates the final T2V prompt generation pipeline:
1. Validates job ownership and analysis readiness
2. Creates a PromptConfig record with user's Step 2 selections
3. Calls MiMo V2.5 Detractor Engine
4. Persists GeneratedPrompt with quality scores
5. Updates Job status
6. Publishes SSE event via Redis
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    AuthorizationError,
    JobNotReadyError,
    NotFoundError,
    PromptGenerationError,
)
from app.core.security import generate_share_token
from app.models.job import AnalysisResult, Job
from app.models.prompt import GeneratedPrompt, PromptConfig
from app.schemas.prompt import (
    GeneratedPromptResponse,
    GeneratePromptRequest,
    MiMoDetractorPayload,
    PromptListResponse,
)
from app.services.mimo_service import mimo_service
from app.services.sse_service import SSEService

logger = logging.getLogger(__name__)


class PromptService:

    @staticmethod
    async def generate_prompt(
        db: AsyncSession,
        request: GeneratePromptRequest,
        user_id: UUID,
    ) -> None:
        """
        Full prompt generation pipeline executed inside a Celery task.
        """
        # ── 1. Fetch and validate job ──────────────────────────────────────────
        result = await db.execute(
            select(Job)
            .where(Job.id == request.job_id)
            .options(selectinload(Job.analysis))
        )
        job: Job | None = result.scalar_one_or_none()

        if job is None:
            raise NotFoundError("Job", str(request.job_id))
        if job.user_id != user_id:
            raise AuthorizationError()
        if not job.is_analysis_ready:
            raise JobNotReadyError(str(request.job_id))

        # ── 2. Fetch analysis ─────────────────────────────────────────────────
        ar_result = await db.execute(
            select(AnalysisResult).where(AnalysisResult.id == request.analysis_id)
        )
        analysis_record: AnalysisResult | None = ar_result.scalar_one_or_none()

        if analysis_record is None:
            raise NotFoundError("AnalysisResult", str(request.analysis_id))

        # ── 3. Create PromptConfig ────────────────────────────────────────────
        now = datetime.now(timezone.utc)
        config = PromptConfig(
            job_id=request.job_id,
            analysis_id=request.analysis_id,
            selected_style=request.selected_style,
            duration=request.duration,
            aspect_ratio=request.aspect_ratio,
            frame_rate=request.frame_rate,
            custom_overrides=request.custom_overrides,
            created_at=now,
        )
        db.add(config)
        await db.flush()  # Populate config.id

        # ── 4. Update job status ──────────────────────────────────────────────
        job.status = "generating_prompt"
        await db.flush()
        await SSEService.publish(
            str(request.job_id),
            {"event": "prompt_generation_started", "job_id": str(request.job_id)},
        )

        # ── 5. Call MiMo V2.5 Detractor Engine ───────────────────────────────
        user_params = {
            "selected_style": request.selected_style,
            "duration": request.duration,
            "aspect_ratio": request.aspect_ratio,
            "frame_rate": request.frame_rate,
            "custom_overrides": request.custom_overrides,
        }

        logger.info(
            "Calling Detractor Engine for job %s (style=%s, duration=%s)",
            request.job_id,
            request.selected_style,
            request.duration,
        )

        try:
            detractor_result: MiMoDetractorPayload = await mimo_service.generate_prompt(
                analysis_payload={
                    "scene_summary": analysis_record.scene_summary,
                    "physical_properties": analysis_record.physical_properties,
                    "style_options": analysis_record.style_options,
                    "physics_flags": analysis_record.physics_flags,
                    "technical_metadata": analysis_record.technical_metadata,
                },
                user_params=user_params,
            )
        except Exception as exc:
            job.status = "analysis_done"  # Roll back to previous stable state
            await db.flush()
            await SSEService.publish(
                str(request.job_id),
                {"event": "prompt_failed", "job_id": str(request.job_id), "error": str(exc)},
            )
            raise PromptGenerationError(detail=str(exc)) from exc

        # ── 6. Persist GeneratedPrompt ────────────────────────────────────────
        generated = GeneratedPrompt(
            job_id=request.job_id,
            config_id=config.id,
            final_prompt=detractor_result.final_prompt,
            prompt_metadata=detractor_result.prompt_metadata.model_dump(),
            physics_score=detractor_result.physics_score,
            quality_score=detractor_result.quality_score,
            share_token=generate_share_token(),  # Pre-generate; public=False until toggled
            is_public=False,
            created_at=now,
        )
        db.add(generated)

        # ── 7. Update Job ─────────────────────────────────────────────────────
        job.status = "prompt_done"
        await db.flush()
        await db.refresh(generated)

        # ── 8. Publish SSE completion ─────────────────────────────────────────
        await SSEService.publish(
            str(request.job_id),
            {
                "event": "prompt_complete",
                "job_id": str(request.job_id),
                "prompt_id": str(generated.id),
                "physics_score": detractor_result.physics_score,
                "quality_score": detractor_result.quality_score,
            },
        )
        logger.info(
            "Prompt generated for job %s (prompt_id=%s, physics=%.2f, quality=%.2f)",
            request.job_id,
            generated.id,
            detractor_result.physics_score,
            detractor_result.quality_score,
        )

    @staticmethod
    async def get_user_prompts(
        db: AsyncSession,
        user_id: UUID,
        page: int = 1,
        per_page: int = 20,
    ) -> PromptListResponse:
        """Paginated list of a user's generated prompts."""
        offset = (page - 1) * per_page

        # Count total
        count_result = await db.execute(
            select(GeneratedPrompt)
            .join(Job, Job.id == GeneratedPrompt.job_id)
            .where(Job.user_id == user_id)
        )
        all_items = count_result.scalars().all()
        total = len(all_items)

        # Fetch page
        page_result = await db.execute(
            select(GeneratedPrompt)
            .join(Job, Job.id == GeneratedPrompt.job_id)
            .where(Job.user_id == user_id)
            .order_by(GeneratedPrompt.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        items = page_result.scalars().all()

        return PromptListResponse(
            items=[GeneratedPromptResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    async def toggle_public(
        db: AsyncSession,
        prompt_id: UUID,
        user_id: UUID,
        make_public: bool,
    ) -> GeneratedPrompt:
        """Toggle public/private sharing for a generated prompt."""
        result = await db.execute(
            select(GeneratedPrompt)
            .join(Job, Job.id == GeneratedPrompt.job_id)
            .where(GeneratedPrompt.id == prompt_id, Job.user_id == user_id)
        )
        prompt: GeneratedPrompt | None = result.scalar_one_or_none()
        if prompt is None:
            raise NotFoundError("GeneratedPrompt", str(prompt_id))

        prompt.is_public = make_public
        if make_public and prompt.share_token is None:
            prompt.share_token = generate_share_token()
        await db.flush()
        return prompt

    @staticmethod
    async def increment_copy_count(db: AsyncSession, prompt_id: UUID) -> None:
        """Increment copy counter (analytics). Non-fatal on failure."""
        try:
            result = await db.execute(
                select(GeneratedPrompt).where(GeneratedPrompt.id == prompt_id)
            )
            prompt = result.scalar_one_or_none()
            if prompt:
                prompt.copy_count += 1
        except Exception as exc:
            logger.warning("Failed to increment copy count for %s: %s", prompt_id, exc)
