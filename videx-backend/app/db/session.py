"""
VIDEX Async Database Session.

Uses SQLAlchemy 2.0 async engine with asyncpg driver.
Tables are created via Alembic migrations in production;
create_db_tables() is used for development convenience.
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

logger = logging.getLogger(__name__)

# ── Engine ────────────────────────────────────────────────────────────────────
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,         # Log SQL queries in debug mode
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,          # Verify connections before use
    pool_recycle=3600,           # Recycle connections every hour
)

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,      # Don't expire attributes after commit
    autocommit=False,
    autoflush=False,
)


async def create_db_tables() -> None:
    """
    Create all tables that don't exist yet.
    In production, use Alembic migrations instead.
    This is a convenience method for dev startup.
    """
    from app.models.base import Base  # noqa: PLC0415
    # Import all models so Base.metadata knows about them
    import app.models.user  # noqa: F401, PLC0415
    import app.models.job   # noqa: F401, PLC0415
    import app.models.prompt  # noqa: F401, PLC0415

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified.")


async def get_db_session() -> AsyncSession:  # type: ignore[return]
    """
    Yield an async SQLAlchemy session.
    Commits on success, rolls back on exception.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_celery_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """
    Returns a fresh sessionmaker with NullPool for use in Celery tasks.
    Celery runs each task in a new asyncio event loop via asyncio.run(),
    which breaks the global engine's connection pool. NullPool prevents this.
    """
    from sqlalchemy.pool import NullPool
    # Pre-load all models to guarantee SQLAlchemy mapper registry initialization
    import app.models.user  # noqa: F401, PLC0415
    import app.models.job   # noqa: F401, PLC0415
    import app.models.prompt  # noqa: F401, PLC0415

    celery_engine = create_async_engine(
        settings.DATABASE_URL,
        poolclass=NullPool,
        echo=settings.DEBUG,
    )
    return async_sessionmaker(
        bind=celery_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
