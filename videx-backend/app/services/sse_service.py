"""
SSE Service — Redis Pub/Sub → Server-Sent Events Bridge.

Enables real-time push updates to the frontend without polling.
Each job has a dedicated Redis channel: "job:{job_id}"

Architecture:
  Celery Worker   →  Redis PUBLISH  →  FastAPI SSE endpoint  →  Browser EventSource
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

# ── Redis connection management ───────────────────────────────────────────────
_redis_clients: dict[int, tuple[asyncio.AbstractEventLoop | None, aioredis.Redis]] = {}


def get_redis() -> aioredis.Redis:
    """
    Get a Redis client bound to the current asyncio event loop.
    This prevents 'attached to a different loop' errors when Celery workers
    create a new event loop for each task via asyncio.run().
    """
    import asyncio  # noqa: PLC0415
    try:
        loop = asyncio.get_running_loop()
        loop_id = id(loop)
    except RuntimeError:
        loop = None
        loop_id = 0

    if loop_id in _redis_clients:
        cached_loop, client = _redis_clients[loop_id]
        if cached_loop is not loop or (loop is not None and loop.is_closed()):
            del _redis_clients[loop_id]

    if loop_id not in _redis_clients:
        client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        _redis_clients[loop_id] = (loop, client)
        
    return _redis_clients[loop_id][1]


class SSEService:
    """
    Static utility class for Redis pub/sub operations.
    Used by Celery workers (publish) and FastAPI SSE endpoints (subscribe).
    """

    @staticmethod
    async def publish(channel: str, data: dict[str, Any]) -> None:
        """
        Publish a JSON event to a Redis channel.
        Called by Celery workers after each pipeline stage.

        Args:
            channel: Job ID string (e.g. "a3f4...") — prefixed internally.
            data: Event payload dict (will be JSON-serialized).
        """
        channel_key = f"job:{channel}"
        message = json.dumps(data)
        
        def _sync_publish() -> None:
            import redis
            # Use synchronous redis to ensure TCP flush before thread exits
            r = redis.Redis.from_url(settings.REDIS_URL)
            r.publish(channel_key, message)
            r.close()

        try:
            import asyncio
            # Run in a thread to prevent blocking FastAPI, but guarantee completion for Celery
            await asyncio.to_thread(_sync_publish)
            logger.debug("SSE published to %s: %s", channel_key, message[:200])
        except Exception as exc:
            # Non-fatal: SSE failure should not block the pipeline
            logger.warning("SSE publish failed for channel %s: %s", channel_key, exc)

    @staticmethod
    async def subscribe(job_id: str) -> AsyncGenerator[dict[str, Any], None]:
        """
        Subscribe to a job's Redis channel and yield parsed events.

        This is an async generator — consumed by the FastAPI SSE endpoint.
        Automatically unsubscribes when the generator is closed (client disconnects).

        Args:
            job_id: The job UUID string.

        Yields:
            Parsed event dicts from the channel.
        """
        redis = get_redis()
        channel_key = f"job:{job_id}"
        pubsub = redis.pubsub()

        try:
            await pubsub.subscribe(channel_key)
            logger.info("SSE subscriber connected to %s", channel_key)

            async for raw_message in pubsub.listen():
                # Skip subscription confirmation messages
                if raw_message["type"] != "message":
                    continue

                try:
                    data = json.loads(raw_message["data"])
                except json.JSONDecodeError:
                    logger.warning("Non-JSON SSE message on %s: %s", channel_key, raw_message["data"])
                    continue

                yield data

                # Auto-close the stream on terminal events
                event_type = data.get("event", "")
                if event_type in {"analysis_failed", "prompt_complete", "prompt_failed"}:
                    logger.info("SSE terminal event received on %s — closing stream.", channel_key)
                    break

        finally:
            await pubsub.unsubscribe(channel_key)
            await pubsub.close()
            logger.info("SSE subscriber disconnected from %s", channel_key)

    @staticmethod
    async def publish_sync(channel: str, data: dict[str, Any]) -> None:
        """
        Synchronous-compatible publish for use inside Celery tasks
        (which run in a sync context but need to push events).
        Uses a fresh Redis connection to avoid event loop conflicts.
        """
        import asyncio  # noqa: PLC0415
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context (shouldn't happen in Celery, but safe)
                await SSEService.publish(channel, data)
            else:
                loop.run_until_complete(SSEService.publish(channel, data))
        except Exception as exc:
            logger.warning("SSE publish_sync failed: %s", exc)
