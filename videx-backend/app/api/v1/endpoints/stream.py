"""
SSE Stream Endpoint.

GET /stream/{job_id} — Subscribe to real-time job status updates.

This endpoint bridges Redis pub/sub to an HTTP Server-Sent Events stream.
The browser's EventSource API connects here and receives events like:
  - analysis_started
  - analysis_complete
  - analysis_failed
  - prompt_generation_started
  - prompt_complete
  - prompt_failed

The stream auto-closes on terminal events.
"""

from __future__ import annotations

import json
import logging
from typing import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.dependencies import CurrentUser, DbSession
from app.services.sse_service import SSEService

logger = logging.getLogger(__name__)
router = APIRouter()


async def _sse_event_stream(job_id: str) -> AsyncGenerator[str, None]:
    """
    Convert SSE service events into the SSE wire format:
    "data: {json}\n\n"
    """
    try:
        async for event_data in SSEService.subscribe(job_id):
            yield f"data: {json.dumps(event_data)}\n\n"
    except Exception as exc:
        logger.error("SSE stream error for job %s: %s", job_id, exc)
        yield f'data: {{"event": "stream_error", "message": "Stream interrupted"}}\n\n'


@router.get(
    "/{job_id}",
    summary="Subscribe to real-time job status events (Server-Sent Events)",
    response_class=StreamingResponse,
)
async def stream_job_events(
    job_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> StreamingResponse:
    """
    SSE endpoint. Connect with EventSource in the browser:

    ```js
    const es = new EventSource(`/api/v1/stream/${jobId}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    es.onmessage = (e) => {
      const data = JSON.parse(e.data);
      // data.event: "analysis_complete" | "prompt_complete" | ...
    };
    ```

    The stream closes automatically when a terminal event is received.
    """
    # Verify the job belongs to the current user before streaming
    from sqlalchemy import select  # noqa: PLC0415
    from app.models.job import Job  # noqa: PLC0415

    result = await db.execute(
        select(Job.id).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    if result.scalar_one_or_none() is None:
        # Return empty stream for unauthorized access (don't reveal 404 on SSE)
        async def empty_stream() -> AsyncGenerator[str, None]:
            yield 'data: {"event": "unauthorized"}\n\n'

        return StreamingResponse(
            empty_stream(),
            media_type="text/event-stream",
        )

    return StreamingResponse(
        _sse_event_stream(str(job_id)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store",
            "X-Accel-Buffering": "no",      # Disable Nginx buffering
            "Connection": "keep-alive",
        },
    )
