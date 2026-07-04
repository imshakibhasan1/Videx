"""
Prompt Pydantic Schemas.
Covers: Step 2 user config request, Step 3 Detractor Engine response,
and prompt history/sharing schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import BaseResponse


# ── Step 3 MiMo Response Sub-models (matches detractor_system.txt) ───────────

class TemporalBeat(BaseModel):
    """One temporal segment of the generated prompt."""
    beat: int
    timecode: str       # e.g. "0:00–0:04"
    description: str


class PromptMetadata(BaseModel):
    """
    Structured metadata from the Detractor Engine.
    Mirrors the detractor_system.txt output schema exactly.
    """
    duration: str
    aspect_ratio: str
    frame_rate: int
    selected_style: str
    camera_specs: str
    lighting_setup: str
    motion_description: str
    color_grade: str
    physics_notes: list[str] = Field(..., min_length=2, max_length=4)
    temporal_structure: list[TemporalBeat] = Field(..., min_length=2, max_length=3)
    recommended_models: list[str] = Field(..., min_length=1, max_length=3)
    tags: list[str] = Field(..., min_length=5, max_length=8)


class MiMoDetractorPayload(BaseModel):
    """
    Complete parsed payload from MiMo V2.5 Step 3 Detractor Engine.
    Strictly matches the schema in detractor_system.txt.
    """
    final_prompt: str = Field(..., min_length=100, max_length=2000)
    prompt_metadata: PromptMetadata
    physics_score: float = Field(..., ge=0.0, le=1.0)
    quality_score: float = Field(..., ge=0.0, le=1.0)


# ── API Request/Response schemas ──────────────────────────────────────────────

StyleChoice = Literal["original", "cinematic", "documentary"]
DurationChoice = Literal["8s", "10s", "15s"]
AspectRatioChoice = Literal["16:9", "9:16", "1:1"]
FrameRateChoice = Literal[24, 30, 60]


class GeneratePromptRequest(BaseModel):
    """
    Request body for POST /prompts/generate.
    Combines analysis result ID with user's Step 2 selections.
    """
    job_id: UUID
    analysis_id: UUID
    selected_style: StyleChoice = "original"
    duration: DurationChoice = "8s"
    aspect_ratio: AspectRatioChoice = "16:9"
    frame_rate: FrameRateChoice = 24
    custom_overrides: dict[str, str] = Field(default_factory=dict)


class GeneratedPromptResponse(BaseResponse):
    """Full response for a generated T2V prompt."""
    prompt_id: UUID = Field(validation_alias="id")
    job_id: UUID
    config_id: UUID

    # The actual prompt
    final_prompt: str
    prompt_metadata: PromptMetadata

    # Quality scores
    physics_score: float
    quality_score: float

    # Sharing
    share_token: str | None
    is_public: bool
    copy_count: int

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromptGenerationJobResponse(BaseResponse):
    """Response for POST /prompts/generate — returns tracking info."""
    job_id: UUID
    config_id: UUID
    status: str = "generating_prompt"
    message: str = "Prompt generation queued. Connect to SSE stream for updates."
    stream_url: str


class PromptListResponse(BaseResponse):
    """Paginated list of a user's generated prompts."""
    items: list[GeneratedPromptResponse]
    total: int
    page: int
    per_page: int


class PromptShareRequest(BaseModel):
    """Request to make a prompt public or private."""
    is_public: bool


class PromptShareResponse(BaseResponse):
    prompt_id: UUID
    is_public: bool
    share_url: str | None
    share_token: str | None


class PublicPromptResponse(BaseResponse):
    """Stripped-down response for anonymous public viewing."""
    final_prompt: str
    prompt_metadata: PromptMetadata
    physics_score: float
    quality_score: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
