"""
Integration tests for the Analysis endpoint.
Uses the full FastAPI app with mocked MiMo service.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Health endpoint returns 200 with status=ok."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "VIDEX"


@pytest.mark.asyncio
async def test_register_new_user(client: AsyncClient):
    """New user registration returns tokens."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Integration Test User",
            "email": "integration@videx.app",
            "password": "Test@1234",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    """Login returns valid tokens for registered user."""
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Login Test", "email": "login@videx.app", "password": "Test@1234"},
    )
    # Then login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@videx.app", "password": "Test@1234"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, auth_headers: dict):
    """GET /auth/me returns current user profile."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@videx.app"


@pytest.mark.asyncio
async def test_upload_signature(client: AsyncClient, auth_headers: dict, mock_cloudinary):
    """Upload signature endpoint returns valid Cloudinary params."""
    response = await client.post(
        "/api/v1/upload/signature",
        json={"filename": "test_video.mp4", "content_type": "video/mp4"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "signature" in data
    assert "job_id" in data
    assert "upload_url" in data


@pytest.mark.asyncio
async def test_upload_requires_auth(client: AsyncClient):
    """Upload endpoint returns 401 without auth."""
    response = await client.post(
        "/api/v1/upload/signature",
        json={"filename": "test.mp4", "content_type": "video/mp4"},
    )
    assert response.status_code == 401
