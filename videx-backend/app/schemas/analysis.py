"""
Analysis Pydantic Schemas.
Mirrors the strict JSON structure enforced in analysis_system.txt.
Used for both MiMo response parsing and API response serialization.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import BaseResponse


# ── Sub-models (matching analysis_system.txt schema) ─────────────────────────

class PhysicalProperties(BaseModel):
    """Physical scene properties extracted by MiMo V2.5."""
    lighting: str
    camera_angle: str
    depth_of_field: str
    motion_blur: str
    color_temperature: str
    environment: str
    time_of_day: str
    weather_conditions: str
    dominant_colors: str | list[str]
    subject_motion: str
    camera_motion: str

    @field_validator("dominant_colors", mode="before")
    @classmethod
    def parse_dominant_colors(cls, v: Any) -> str:
        """MiMo occasionally returns a list instead of a string despite the prompt."""
        if isinstance(v, list):
            return ", ".join(str(item) for item in v)
        return str(v)


class StyleOption(BaseModel):
    """One of three style options returned by the analysis engine."""
    id: str = Field(..., pattern="^(original|cinematic|documentary)$")
    label: str
    description: str
    mood_tags: list[str] = Field(..., min_length=2, max_length=4)
    color_grading: str
    camera_movement: str
    lighting_recipe: str


class PhysicsFlags(BaseModel):
    """Physics compliance observations from the analysis."""
    gravity_compliance: str
    fluid_dynamics: str
    lighting_physics: str
    motion_physics: str


class TechnicalMetadata(BaseModel):
    """Technical video metadata detected by MiMo."""
    estimated_codec: str
    aspect_ratio_detected: str
    estimated_frame_rate: int
    video_quality: str = Field(..., pattern="^(Excellent|Good|Fair|Poor)$")
    recommended_models: list[str] = Field(..., min_length=2, max_length=3)


class MiMoAnalysisPayload(BaseModel):
    """
    Complete parsed payload from MiMo V2.5 Step 1 analysis.
    Strictly matches the schema in analysis_system.txt.
    """
    scene_summary: str = Field(..., min_length=50)
    physical_properties: PhysicalProperties
    style_options: list[StyleOption] = Field(..., min_length=3, max_length=3)
    physics_flags: PhysicsFlags
    technical_metadata: TechnicalMetadata
    confidence_score: float = Field(..., ge=0.0, le=1.0)

    @field_validator("style_options")
    @classmethod
    def validate_style_ids(cls, v: list[StyleOption]) -> list[StyleOption]:
        required_ids = {"original", "cinematic", "documentary"}
        actual_ids = {opt.id for opt in v}
        if actual_ids != required_ids:
            raise ValueError(
                f"style_options must contain exactly: {required_ids}. Got: {actual_ids}"
            )
        return v


# ── API Request/Response schemas ──────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    """Request body for POST /analyze."""
    job_id: UUID


class AnalysisResultResponse(BaseResponse):
    """API response for GET /analyze/{job_id}."""
    analysis_id: UUID
    job_id: UUID
    scene_summary: str
    physical_properties: PhysicalProperties
    style_options: list[StyleOption]
    physics_flags: PhysicsFlags
    technical_metadata: TechnicalMetadata
    confidence_score: float

    model_config = ConfigDict(from_attributes=True)


class AnalysisJobResponse(BaseResponse):
    """Response for POST /analyze — returns job tracking info."""
    job_id: UUID
    status: str
    message: str = "Analysis queued. Connect to SSE stream for real-time updates."
    stream_url: str  # /api/v1/stream/{job_id}
