"""
Integration tests for the Prompt endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient

from app.models.job import Job, AnalysisResult


@pytest.mark.asyncio
async def test_generate_prompt_accepted(client: AsyncClient, db, test_user, auth_headers):
    """Generate prompt endpoint returns 202 Accepted and queues the task."""
    job_id = uuid.uuid4()
    analysis_id = uuid.uuid4()
    
    # Setup prerequisite data
    job = Job(id=job_id, user_id=test_user.id, status="analysis_done", cloudinary_url="test", cloudinary_public_id="test")
    analysis = AnalysisResult(
        id=analysis_id,
        job_id=job_id,
        scene_summary="Test scene",
        physical_properties={},
        style_options=[],
        physics_flags={},
        technical_metadata={},
        confidence_score=0.9,
        created_at=datetime.now(timezone.utc)
    )
    db.add(job)
    db.add(analysis)
    await db.commit()

    with __import__("unittest.mock").patch("app.api.v1.endpoints.prompts.run_prompt_generation.apply_async") as mock_task:
        response = await client.post(
            "/api/v1/prompts/generate",
            json={
                "job_id": str(job_id),
                "analysis_id": str(analysis_id),
                "selected_style": "cinematic",
                "duration": "10s",
                "aspect_ratio": "16:9",
                "frame_rate": 24
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["job_id"] == str(job_id)
        assert data["status"] == "generating_prompt"
        mock_task.assert_called_once()


@pytest.mark.asyncio
async def test_list_prompts_empty(client: AsyncClient, auth_headers):
    """Listing prompts for a user with no prompts returns empty list."""
    response = await client.get("/api/v1/prompts/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
