"""
VIDEX Application Configuration.

All settings are loaded from environment variables.
Use `.env` for local development, Render/Railway secrets for production.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import ClassVar

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "VIDEX"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str  # postgresql+asyncpg://...

    # ── Redis ────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Cloudinary ───────────────────────────────────────────────────────────
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    CLOUDINARY_MAX_BYTES: int = 52_428_800   # 50 MB hard limit
    CLOUDINARY_MAX_DURATION: int = 15        # 15 seconds hard limit
    CLOUDINARY_FOLDER: str = "videx/uploads"
    CLOUDINARY_TTL_SECONDS: int = 86_400     # URL expires after 24 hours

    # ── MiMo V2.5 ────────────────────────────────────────────────────────────
    MIMO_API_KEY: str
    MIMO_API_URL: str = "https://api.xiaomimimo.com/v1/chat/completions"
    MIMO_MODEL: str = "mimo-v2.5"
    MIMO_MAX_TOKENS: int = 2048
    MIMO_TIMEOUT: float = 120.0
    MIMO_FPS: int = 2                        # Frames per second for video analysis
    MIMO_MEDIA_RESOLUTION: str = "default"
    MIMO_MAX_RETRIES: int = 3               # Tenacity retry count on transient errors

    # ── Celery ───────────────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_SOFT_TIME_LIMIT: int = 150  # seconds before SoftTimeLimitExceeded
    CELERY_TASK_TIME_LIMIT: int = 180       # hard kill limit

    # ── JWT ──────────────────────────────────────────────────────────────────
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Rate Limiting (Free Tier MVP) ─────────────────────────────────────────
    RATE_LIMIT_UPLOADS_PER_HOUR: int = 10
    RATE_LIMIT_PROMPTS_PER_DAY: int = 50

    # ── Prompts ───────────────────────────────────────────────────────────────
    # ClassVar: not treated as a settings field — computed at class level
    PROMPTS_DIR: ClassVar[Path] = Path(__file__).parent / "core" / "prompts"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list[str]) -> list[str]:
        """Accept both comma-separated string and list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def analysis_system_prompt(self) -> str:
        """Load Step 1 analysis system prompt from disk (cached by Python)."""
        return (self.PROMPTS_DIR / "analysis_system.txt").read_text(encoding="utf-8")

    @property
    def detractor_system_prompt(self) -> str:
        """Load Step 3 detractor engine prompt from disk (cached by Python)."""
        return (self.PROMPTS_DIR / "detractor_system.txt").read_text(encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — safe to import anywhere."""
    return Settings()  # type: ignore[call-arg]


settings: Settings = get_settings()
