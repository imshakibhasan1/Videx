"""
Celery Application Configuration.

Uses Redis as both broker and result backend.
Workers run in a separate Docker container (Dockerfile.worker).
"""

from __future__ import annotations

from celery import Celery

from app.config import settings

celery_app = Celery(
    "videx",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.analyze_task",
        "app.tasks.prompt_task",
    ],
)

celery_app.conf.update(
    # ── Serialization ──────────────────────────────────────────────────────────
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # ── Timezone ───────────────────────────────────────────────────────────────
    timezone="UTC",
    enable_utc=True,
    # ── Task timeouts ──────────────────────────────────────────────────────────
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    # ── Result expiry ──────────────────────────────────────────────────────────
    result_expires=3600,  # Celery results expire after 1 hour
    # ── Retry policy ──────────────────────────────────────────────────────────
    task_acks_late=True,          # Ack after task completes (not on receipt)
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1, # Prevent task hoarding
    # ── Routing ───────────────────────────────────────────────────────────────
    task_routes={
        "app.tasks.analyze_task.*": {"queue": "analysis"},
        "app.tasks.prompt_task.*": {"queue": "prompts"},
    },
    # ── Monitoring ────────────────────────────────────────────────────────────
    worker_send_task_events=True,
    task_send_sent_event=True,
)
