"""
VIDEX Custom Exception Hierarchy.

All domain exceptions extend VidexBaseException, which is caught
by the global exception handler in main.py and serialized into
a consistent { error, message, detail } JSON envelope.
"""

from __future__ import annotations

from fastapi import status


class VidexBaseException(Exception):
    """Root exception — all VIDEX domain errors extend this."""

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        detail: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.detail = detail
        super().__init__(message)


# ── 4xx Client Errors ─────────────────────────────────────────────────────────

class ValidationError(VidexBaseException):
    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, "VALIDATION_ERROR", message, detail)


class AuthenticationError(VidexBaseException):
    def __init__(
        self,
        message: str = "Authentication failed.",
        detail: str | None = None,
    ) -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, "AUTHENTICATION_ERROR", message, detail)


class AuthorizationError(VidexBaseException):
    def __init__(
        self,
        message: str = "You do not have permission to perform this action.",
        detail: str | None = None,
    ) -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, "AUTHORIZATION_ERROR", message, detail)


class NotFoundError(VidexBaseException):
    def __init__(self, resource: str, resource_id: str | None = None) -> None:
        detail = (
            f"{resource} with id '{resource_id}' was not found."
            if resource_id
            else f"{resource} was not found."
        )
        super().__init__(status.HTTP_404_NOT_FOUND, "NOT_FOUND", f"{resource} not found.", detail)


class RateLimitError(VidexBaseException):
    def __init__(
        self,
        message: str = "Rate limit exceeded. Please wait before making more requests.",
        detail: str | None = None,
    ) -> None:
        super().__init__(
            status.HTTP_429_TOO_MANY_REQUESTS, "RATE_LIMIT_EXCEEDED", message, detail
        )


class UploadError(VidexBaseException):
    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "UPLOAD_ERROR", message, detail
        )


# ── 5xx Server / Upstream Errors ──────────────────────────────────────────────

class AnalysisError(VidexBaseException):
    def __init__(self, message: str = "Video analysis failed.", detail: str | None = None) -> None:
        super().__init__(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "ANALYSIS_ERROR", message, detail
        )


class PromptGenerationError(VidexBaseException):
    def __init__(
        self, message: str = "Prompt generation failed.", detail: str | None = None
    ) -> None:
        super().__init__(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "PROMPT_GENERATION_ERROR", message, detail
        )


class MiMoAPIError(VidexBaseException):
    def __init__(
        self, message: str = "AI engine is temporarily unavailable.", detail: str | None = None
    ) -> None:
        super().__init__(status.HTTP_502_BAD_GATEWAY, "MIMO_API_ERROR", message, detail)


class MiMoResponseParseError(VidexBaseException):
    def __init__(self, detail: str | None = None) -> None:
        super().__init__(
            status.HTTP_502_BAD_GATEWAY,
            "MIMO_PARSE_ERROR",
            "AI engine returned an unexpected response format.",
            detail,
        )


class CloudinaryError(VidexBaseException):
    def __init__(self, message: str = "Media storage error.", detail: str | None = None) -> None:
        super().__init__(
            status.HTTP_502_BAD_GATEWAY, "CLOUDINARY_ERROR", message, detail
        )


class JobNotReadyError(VidexBaseException):
    def __init__(self, job_id: str) -> None:
        super().__init__(
            status.HTTP_409_CONFLICT,
            "JOB_NOT_READY",
            "This job is still processing.",
            f"Job {job_id} has not completed analysis yet.",
        )
