"""
Celery Task — Prompt Generation (Step 3).

Runs in the 'prompts' queue worker.
Bridges the synchronous Celery context to the async prompt service.
"""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


class PromptTask(Task):
    """Custom task class for prompt generation jobs."""
    abstract = True

    def on_failure(self, exc: Exception, task_id: str, args: list, kwargs: dict, einfo) -> None:  # type: ignore[override]
        logger.error("Prompt task %s failed: %s", task_id, exc)
        super().on_failure(exc, task_id, args, kwargs, einfo)


@celery_app.task(
    bind=True,
    base=PromptTask,
    name="app.tasks.prompt_task.run_prompt_generation",
    queue="prompts",
    max_retries=2,
    default_retry_delay=15,
)
def run_prompt_generation(
    self: Task,
    job_id_str: str,
    analysis_id_str: str,
    user_id_str: str,
    selected_style: str,
    duration: str,
    aspect_ratio: str,
    frame_rate: int,
    custom_overrides: dict,
) -> dict:  # type: ignore[return]
    """
    Celery task: Run the full Step 3 Detractor Engine pipeline.

    Args:
        job_id_str: Job UUID string
        analysis_id_str: AnalysisResult UUID string
        user_id_str: User UUID string
        selected_style: "original" | "cinematic" | "documentary"
        duration: "8s" | "10s" | "15s"
        aspect_ratio: "16:9" | "9:16" | "1:1"
        frame_rate: 24 | 30 | 60
        custom_overrides: dict of custom prompt overrides

    Returns:
        dict with job_id and prompt_id on success
    """
    from app.db.session import get_celery_sessionmaker  # noqa: PLC0415
    from app.schemas.prompt import GeneratePromptRequest  # noqa: PLC0415
    from app.services.prompt_service import PromptService  # noqa: PLC0415

    request = GeneratePromptRequest(
        job_id=UUID(job_id_str),
        analysis_id=UUID(analysis_id_str),
        selected_style=selected_style,  # type: ignore[arg-type]
        duration=duration,  # type: ignore[arg-type]
        aspect_ratio=aspect_ratio,  # type: ignore[arg-type]
        frame_rate=frame_rate,  # type: ignore[arg-type]
        custom_overrides=custom_overrides,
    )
    user_id = UUID(user_id_str)

    async def _run() -> dict:
        sessionmaker = get_celery_sessionmaker()
        async with sessionmaker() as db:
            try:
                await PromptService.generate_prompt(db, request, user_id)
                await db.commit()
                return {"job_id": job_id_str, "status": "prompt_done"}
            except SoftTimeLimitExceeded:
                logger.error("Prompt task soft time limit exceeded for job %s", job_id_str)
                await db.rollback()
                raise
            except Exception as exc:
                await db.rollback()
                logger.exception("Prompt pipeline error for job %s: %s", job_id_str, exc)
                raise self.retry(exc=exc, countdown=min(15 * (self.request.retries + 1), 90)) from exc
            finally:
                await sessionmaker.kw["bind"].dispose()

    return asyncio.run(_run())
