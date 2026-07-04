"""
Pytest Configuration & Shared Fixtures.
"""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.base import Base
from app.models.user import User
from app.core.security import create_access_token, get_password_hash

# ── Test Database ─────────────────────────────────────────────────────────────
TEST_DB_URL = "postgresql+asyncpg://user:pass@localhost:5432/videx_test"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create all tables before test session, drop after."""
    import app.models.user   # noqa: F401
    import app.models.job    # noqa: F401
    import app.models.prompt # noqa: F401

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional test database session that rolls back after each test."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    """Create a test user in the database."""
    user = User(
        email="test@videx.app",
        name="Test User",
        hashed_password=get_password_hash("Test@1234"),
        provider="email",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict[str, str]:
    """Return Authorization headers for the test user."""
    token = create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def client(db: AsyncSession, auth_headers: dict[str, str]) -> AsyncGenerator[AsyncClient, None]:
    """Async test client with injected DB session."""
    from app.dependencies import get_db  # noqa: PLC0415

    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def mock_mimo_service():
    """Mock the MiMo V2.5 service for unit tests."""
    with __import__("unittest.mock", fromlist=["patch"]).patch(
        "app.services.mimo_service.mimo_service"
    ) as mock:
        mock.analyze_video = AsyncMock()
        mock.generate_prompt = AsyncMock()
        yield mock


@pytest.fixture
def mock_cloudinary():
    """Mock Cloudinary operations for unit tests."""
    with __import__("unittest.mock", fromlist=["patch"]).patch(
        "cloudinary.utils.api_sign_request", return_value="mock_signature"
    ):
        yield
