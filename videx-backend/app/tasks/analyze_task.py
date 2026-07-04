"""
Celery Task — Video Analysis (Step 1).

Runs in the 'analysis' queue worker.
Bridges the synchronous Celery context to the async analysis service.
"""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


class AnalysisTask(Task):
    """Custom task class with database session lifecycle management."""
    abstract = True

    def on_failure(self, exc: Exception, task_id: str, args: list, kwargs: dict, einfo) -> None:  # type: ignore[override]
        logger.error("Analysis task %s failed: %s", task_id, exc)
        super().on_failure(exc, task_id, args, kwargs, einfo)


@celery_app.task(
    bind=True,
    base=AnalysisTask,
    name="app.tasks.analyze_task.run_video_analysis",
    queue="analysis",
    max_retries=2,
    default_retry_delay=10,
)
def run_video_analysis(self: Task, job_id_str: str, user_id_str: str) -> dict:  # type: ignore[return]
    """
    Celery task: Run the full Step 1 video analysis pipeline.

    Args:
        job_id_str: Job UUID as string (Celery serializes all args as JSON)
        user_id_str: User UUID as string

    Returns:
        dict with job_id and analysis_id on success
    """
    from app.db.session import get_celery_sessionmaker  # noqa: PLC0415
    from app.services.analysis_service import AnalysisService  # noqa: PLC0415

    job_id = UUID(job_id_str)
    user_id = UUID(user_id_str)

    async def _run() -> dict:
        sessionmaker = get_celery_sessionmaker()
        async with sessionmaker() as db:
            try:
                await AnalysisService.run_analysis(db, job_id, user_id)
                await db.commit()
                return {"job_id": job_id_str, "status": "analysis_done"}
            except SoftTimeLimitExceeded:
                logger.error("Analysis task soft time limit exceeded for job %s", job_id_str)
                await db.rollback()
                raise
            except Exception as exc:
                await db.rollback()
                logger.exception("Analysis pipeline error for job %s: %s", job_id_str, exc)
                # Retry with exponential backoff for transient failures
                raise self.retry(exc=exc, countdown=min(10 * (self.request.retries + 1), 60)) from exc
            finally:
                # Close NullPool engine to prevent resource leaks
                await sessionmaker.kw["bind"].dispose()

    return asyncio.run(_run())
