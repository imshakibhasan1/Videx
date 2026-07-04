"""Unit tests for Prompt Service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import AuthorizationError, JobNotReadyError, NotFoundError
from app.models.job import Job, AnalysisResult
from app.schemas.prompt import GeneratePromptRequest
from app.services.prompt_service import PromptService


@pytest.mark.asyncio
async def test_generate_prompt_job_not_found(db):
    """Raises NotFoundError if job does not exist."""
    request = GeneratePromptRequest(
        job_id=uuid.uuid4(),
        analysis_id=uuid.uuid4(),
    )
    with pytest.raises(NotFoundError, match="Job"):
        await PromptService.generate_prompt(db, request, uuid.uuid4())


@pytest.mark.asyncio
async def test_generate_prompt_unauthorized(db, test_user):
    """Raises AuthorizationError if user does not own the job."""
    other_user_id = uuid.uuid4()
    job = Job(id=uuid.uuid4(), user_id=other_user_id, status="analysis_done", cloudinary_url="", cloudinary_public_id="")
    db.add(job)
    await db.commit()

    request = GeneratePromptRequest(
        job_id=job.id,
        analysis_id=uuid.uuid4(),
    )
    with pytest.raises(AuthorizationError):
        await PromptService.generate_prompt(db, request, test_user.id)


@pytest.mark.asyncio
async def test_generate_prompt_job_not_ready(db, test_user):
    """Raises JobNotReadyError if analysis is not complete."""
    job = Job(id=uuid.uuid4(), user_id=test_user.id, status="processing", cloudinary_url="", cloudinary_public_id="")
    db.add(job)
    await db.commit()

    request = GeneratePromptRequest(
        job_id=job.id,
        analysis_id=uuid.uuid4(),
    )
    with pytest.raises(JobNotReadyError):
        await PromptService.generate_prompt(db, request, test_user.id)


@pytest.mark.asyncio
async def test_generate_prompt_analysis_not_found(db, test_user):
    """Raises NotFoundError if analysis result does not exist."""
    job = Job(id=uuid.uuid4(), user_id=test_user.id, status="analysis_done", cloudinary_url="", cloudinary_public_id="")
    db.add(job)
    await db.commit()

    request = GeneratePromptRequest(
        job_id=job.id,
        analysis_id=uuid.uuid4(),
    )
    with pytest.raises(NotFoundError, match="AnalysisResult"):
        await PromptService.generate_prompt(db, request, test_user.id)
