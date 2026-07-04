"""
Prompt Endpoints.

POST /prompts/generate    — Trigger Step 3 Detractor Engine
GET  /prompts/            — List user's generated prompts (paginated)
GET  /prompts/{prompt_id} — Get a single generated prompt
POST /prompts/{prompt_id}/share — Toggle public sharing
POST /prompts/{prompt_id}/copy  — Track copy event
GET  /prompts/public/{share_token} — View a public prompt (no auth)
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, status
from sqlalchemy import select

from app.core.exceptions import NotFoundError
from app.dependencies import CurrentUser, DbSession
from app.models.prompt import GeneratedPrompt
from app.schemas.prompt import (
    GeneratePromptRequest,
    GeneratedPromptResponse,
    PromptGenerationJobResponse,
    PromptListResponse,
    PromptShareRequest,
    PromptShareResponse,
    PublicPromptResponse,
)
from app.services.prompt_service import PromptService
from app.tasks.prompt_task import run_prompt_generation

router = APIRouter()


@router.post(
    "/generate",
    response_model=PromptGenerationJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger Step 3 Detractor Engine",
)
async def generate_prompt(
    body: GeneratePromptRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> PromptGenerationJobResponse:
    """
    Dispatch the Step 3 prompt generation Celery task.

    Requires the job to have completed Step 1 analysis.
    Returns immediately (HTTP 202) — subscribe to SSE for completion.
    """
    # Dispatch Celery task
    celery_task = run_prompt_generation.apply_async(
        kwargs={
            "job_id_str": str(body.job_id),
            "analysis_id_str": str(body.analysis_id),
            "user_id_str": str(current_user.id),
            "selected_style": body.selected_style,
            "duration": body.duration,
            "aspect_ratio": body.aspect_ratio,
            "frame_rate": body.frame_rate,
            "custom_overrides": body.custom_overrides,
        },
        queue="prompts",
    )

    return PromptGenerationJobResponse(
        job_id=body.job_id,
        config_id=body.analysis_id,  # Placeholder — actual config_id assigned inside task
        status="generating_prompt",
        message="Prompt generation queued. Subscribe to SSE for real-time updates.",
        stream_url=f"/api/v1/stream/{body.job_id}",
    )


@router.get(
    "/",
    response_model=PromptListResponse,
    summary="List all generated prompts for the authenticated user",
)
async def list_prompts(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> PromptListResponse:
    """Return a paginated list of the user's generated prompts, newest first."""
    return await PromptService.get_user_prompts(db, current_user.id, page, per_page)


@router.get(
    "/{prompt_id}",
    response_model=GeneratedPromptResponse,
    summary="Get a single generated prompt by ID",
)
async def get_prompt(
    prompt_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> GeneratedPromptResponse:
    """Fetch full details of a generated prompt owned by the current user."""
    from app.models.job import Job  # noqa: PLC0415

    result = await db.execute(
        select(GeneratedPrompt)
        .join(Job, Job.id == GeneratedPrompt.job_id)
        .where(GeneratedPrompt.id == prompt_id, Job.user_id == current_user.id)
    )
    prompt: GeneratedPrompt | None = result.scalar_one_or_none()
    if prompt is None:
        raise NotFoundError("GeneratedPrompt", str(prompt_id))

    return GeneratedPromptResponse.model_validate(prompt)


@router.post(
    "/{prompt_id}/share",
    response_model=PromptShareResponse,
    summary="Toggle public sharing for a prompt",
)
async def toggle_share(
    prompt_id: UUID,
    body: PromptShareRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> PromptShareResponse:
    """Make a prompt public (generates a share link) or private."""
    prompt = await PromptService.toggle_public(db, prompt_id, current_user.id, body.is_public)
    share_url = (
        f"https://videx.app/share/{prompt.share_token}" if prompt.is_public and prompt.share_token else None
    )
    return PromptShareResponse(
        prompt_id=prompt.id,
        is_public=prompt.is_public,
        share_url=share_url,
        share_token=prompt.share_token,
    )


@router.post(
    "/{prompt_id}/copy",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Track a copy event for analytics",
)
async def track_copy(
    prompt_id: UUID,
    db: DbSession,
) -> None:
    """Increment the copy counter. No auth required (anonymous copy tracking)."""
    await PromptService.increment_copy_count(db, prompt_id)


@router.get(
    "/public/{share_token}",
    response_model=PublicPromptResponse,
    summary="View a public prompt via share token (no auth required)",
)
async def get_public_prompt(
    share_token: str,
    db: DbSession,
) -> PublicPromptResponse:
    """Fetch a publicly shared prompt by its share token. No authentication required."""
    result = await db.execute(
        select(GeneratedPrompt).where(
            GeneratedPrompt.share_token == share_token,
            GeneratedPrompt.is_public.is_(True),
        )
    )
    prompt: GeneratedPrompt | None = result.scalar_one_or_none()
    if prompt is None:
        raise NotFoundError("Shared prompt")

    return PublicPromptResponse.model_validate(prompt)
