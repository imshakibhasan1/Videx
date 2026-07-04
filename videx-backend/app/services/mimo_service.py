"""
MiMo V2.5 API Service — The AI Engine Client.

This is the most critical service in VIDEX. It wraps the Xiaomi MiMo V2.5
API with:
  - Strict JSON response enforcement (response_format: json_object)
  - Pydantic validation of the returned payload against our schema contracts
  - Tenacity retry logic for transient upstream failures
  - Detailed error propagation for debugging

Both Step 1 (Analysis) and Step 3 (Detractor Engine) calls are handled here.
The system prompts are loaded from disk via settings properties.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings
from app.core.exceptions import MiMoAPIError, MiMoResponseParseError
from app.schemas.analysis import MiMoAnalysisPayload
from app.schemas.prompt import MiMoDetractorPayload

logger = logging.getLogger(__name__)

# ── Retry strategy: exponential backoff for transient HTTP errors ──────────────
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in _RETRYABLE_STATUS_CODES
    return isinstance(exc, (httpx.TimeoutException, httpx.NetworkError))


class MiMoService:
    """
    Async client for the MiMo V2.5 API.
    Uses a single shared httpx.AsyncClient for connection pooling.
    """

    def __init__(self) -> None:
        # Cache tuples of (loop, client) to handle memory address reuse
        self._clients: dict[int, tuple[asyncio.AbstractEventLoop | None, httpx.AsyncClient]] = {}

    def _get_client(self) -> httpx.AsyncClient:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop_id = id(loop)
        except RuntimeError:
            loop = None
            loop_id = 0

        if loop_id in self._clients:
            cached_loop, client = self._clients[loop_id]
            # If the loop was closed, or if the memory address was reused for a new loop
            if cached_loop is not loop or (loop is not None and loop.is_closed()):
                del self._clients[loop_id]

        if loop_id not in self._clients:
            client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=10.0,
                    read=settings.MIMO_TIMEOUT,
                    write=10.0,
                    pool=5.0,
                ),
                headers={
                    "Authorization": f"Bearer {settings.MIMO_API_KEY}",
                    "Content-Type": "application/json",
                    "User-Agent": f"VIDEX/{settings.APP_VERSION}",
                },
            )
            self._clients[loop_id] = (loop, client)
            
        return self._clients[loop_id][1]

    async def close(self) -> None:
        """Close the underlying HTTP client. Call during app shutdown."""
        for _, client in self._clients.values():
            await client.aclose()
        self._clients.clear()

    # ── Step 1: Video Analysis ─────────────────────────────────────────────────

    async def analyze_video(self, video_url: str) -> MiMoAnalysisPayload:
        """
        Send a Cloudinary video URL to MiMo V2.5 for analysis.

        Returns a fully validated MiMoAnalysisPayload.
        Raises MiMoAPIError or MiMoResponseParseError on failure.
        """
        system_prompt = settings.analysis_system_prompt
        user_message = self._build_video_message(
            video_url=video_url,
            text="Analyze this video and return the structured JSON exactly as specified in your instructions.",
        )
        raw_response = await self._call_mimo(
            system_prompt=system_prompt,
            user_message=user_message,
            operation="video_analysis",
        )
        return self._parse_analysis_response(raw_response)

    # ── Step 3: Detractor Prompt Engine ────────────────────────────────────────

    async def generate_prompt(
        self,
        analysis_payload: dict[str, Any],
        user_params: dict[str, Any],
    ) -> MiMoDetractorPayload:
        """
        Send the Step 1 analysis + user params to the Detractor Engine.

        Returns a fully validated MiMoDetractorPayload.
        """
        system_prompt = settings.detractor_system_prompt
        input_payload = {
            "analysis": analysis_payload,
            "user_params": user_params,
        }
        user_message = [
            {
                "type": "text",
                "text": (
                    f"Generate the T2V prompt from this input:\n\n"
                    f"{json.dumps(input_payload, indent=2)}\n\n"
                    "Return the structured JSON exactly as specified in your instructions."
                ),
            }
        ]
        raw_response = await self._call_mimo(
            system_prompt=system_prompt,
            user_message=user_message,
            operation="prompt_generation",
        )
        return self._parse_detractor_response(raw_response)

    # ── Core HTTP call ─────────────────────────────────────────────────────────

    @retry(
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(settings.MIMO_MAX_RETRIES),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        reraise=True,
    )
    async def _call_mimo(
        self,
        system_prompt: str,
        user_message: list[dict[str, Any]],
        operation: str,
    ) -> str:
        """
        Execute a single MiMo API request with retry logic.

        Returns the raw string content from the model's response.
        """
        payload: dict[str, Any] = {
            "model": settings.MIMO_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "max_completion_tokens": settings.MIMO_MAX_TOKENS,
            # Force JSON-only output — critical for preventing hallucinations
            "response_format": {"type": "json_object"},
            # Deterministic output: low temperature for factual extraction
            "temperature": 0.1,
        }

        logger.info("MiMo API call: operation=%s model=%s", operation, settings.MIMO_MODEL)

        try:
            client = self._get_client()
            response = await client.post(settings.MIMO_API_URL, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "MiMo API HTTP error: status=%d body=%s",
                exc.response.status_code,
                exc.response.text[:500],
            )
            if not _is_retryable(exc):
                raise MiMoAPIError(
                    detail=f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"
                ) from exc
            raise
        except httpx.TimeoutException as exc:
            logger.error("MiMo API timeout after %ss on operation=%s", settings.MIMO_TIMEOUT, operation)
            raise MiMoAPIError(
                message="AI engine timed out. Please try again.",
                detail=str(exc),
            ) from exc

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise MiMoAPIError(detail="MiMo returned empty choices array.")

        content: str = choices[0].get("message", {}).get("content", "")
        if not content:
            raise MiMoAPIError(detail="MiMo returned empty message content.")

        logger.info(
            "MiMo API success: operation=%s tokens_used=%s",
            operation,
            data.get("usage", {}).get("total_tokens", "unknown"),
        )
        return content

    # ── Response parsing & validation ─────────────────────────────────────────

    def _parse_analysis_response(self, raw: str) -> MiMoAnalysisPayload:
        """
        Parse and validate the Step 1 analysis JSON from MiMo.
        Raises MiMoResponseParseError if the schema is violated.
        """
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("MiMo analysis response is not valid JSON: %s", raw[:500])
            raise MiMoResponseParseError(
                detail=f"JSON parse error: {exc}. Raw response (first 300 chars): {raw[:300]}"
            ) from exc

        try:
            return MiMoAnalysisPayload.model_validate(data)
        except Exception as exc:
            logger.error("MiMo analysis schema validation failed: %s", exc)
            raise MiMoResponseParseError(
                detail=f"Schema validation error: {exc}"
            ) from exc

    def _parse_detractor_response(self, raw: str) -> MiMoDetractorPayload:
        """
        Parse and validate the Step 3 Detractor Engine JSON from MiMo.
        Raises MiMoResponseParseError if the schema is violated.
        """
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("MiMo detractor response is not valid JSON: %s", raw[:500])
            raise MiMoResponseParseError(
                detail=f"JSON parse error: {exc}. Raw response (first 300 chars): {raw[:300]}"
            ) from exc

        try:
            return MiMoDetractorPayload.model_validate(data)
        except Exception as exc:
            logger.error("MiMo detractor schema validation failed: %s", exc)
            raise MiMoResponseParseError(
                detail=f"Schema validation error: {exc}"
            ) from exc

    # ── Video message builder ─────────────────────────────────────────────────

    def _build_video_message(self, video_url: str, text: str) -> list[dict[str, Any]]:
        """Build the multimodal user message with video URL + instruction text."""
        return [
            {
                "type": "video_url",
                "video_url": {"url": video_url},
                "fps": settings.MIMO_FPS,
                "media_resolution": settings.MIMO_MEDIA_RESOLUTION,
            },
            {
                "type": "text",
                "text": text,
            },
        ]


# ── Module-level singleton (import and reuse) ─────────────────────────────────
mimo_service = MiMoService()
