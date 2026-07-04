"""Unit tests for MiMo V2.5 Service."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import MiMoAPIError, MiMoResponseParseError
from app.services.mimo_service import MiMoService


VALID_ANALYSIS_JSON = {
    "scene_summary": "A golden-hour urban street scene where a young woman in a red coat walks confidently through a busy intersection, cars passing in the background as warm sunlight illuminates the environment.",
    "physical_properties": {
        "lighting": "Natural golden-hour backlight at approximately 2800K, soft diffused shadows",
        "camera_angle": "Eye-level, slight low angle at approximately 5 degrees below",
        "depth_of_field": "Shallow DOF, subject sharp, background bokeh at estimated f/2.0",
        "motion_blur": "Moderate horizontal trailing on moving vehicles at 1/60s equivalent",
        "color_temperature": "2800–3200K, warm golden hour",
        "environment": "Outdoor urban street, city intersection, late afternoon",
        "time_of_day": "Golden Hour",
        "weather_conditions": "Clear",
        "dominant_colors": "#F4A261 (warm amber), #2D3561 (deep navy), #E8E8E8 (neutral grey)",
        "subject_motion": "Subject walking left-to-right at approximately 1.2 m/s",
        "camera_motion": "Static tripod mount",
    },
    "style_options": [
        {
            "id": "original",
            "label": "Original Style",
            "description": "Faithful reconstruction preserving the warm golden hour natural aesthetic.",
            "mood_tags": ["naturalistic", "warm", "authentic"],
            "color_grading": "True-to-life colors, natural skin tones, minimal processing",
            "camera_movement": "Static, tripod-mounted",
            "lighting_recipe": "Available golden hour light only",
        },
        {
            "id": "cinematic",
            "label": "Cinematic Alternate",
            "description": "Elevated anamorphic cinema version with dramatic lens flares.",
            "mood_tags": ["dramatic", "cinematic", "golden"],
            "color_grading": "Teal-orange grade, crushed blacks, Kodak Vision3 emulation",
            "camera_movement": "Slow motivated push-in at 0.3 m/s",
            "lighting_recipe": "Enhanced rim light, optional haze for atmosphere",
        },
        {
            "id": "documentary",
            "label": "Documentary Style",
            "description": "Verite handheld approach, raw and observational.",
            "mood_tags": ["raw", "journalistic", "authentic"],
            "color_grading": "Desaturated, flat, journalistic look",
            "camera_movement": "Handheld, reactive follow",
            "lighting_recipe": "Available light only, accept exposure imperfections",
        },
    ],
    "physics_flags": {
        "gravity_compliance": "Normal gravitational behavior, natural walking gait confirmed",
        "fluid_dynamics": "N/A",
        "lighting_physics": "Shadow direction consistent with single backlight source",
        "motion_physics": "Subject movement speed consistent with natural walking at 1.2 m/s",
    },
    "technical_metadata": {
        "estimated_codec": "Sony FX3, S-Log3, 4K/24p",
        "aspect_ratio_detected": "16:9",
        "estimated_frame_rate": 24,
        "video_quality": "Excellent",
        "recommended_models": ["Sora", "Kling 2.0"],
    },
    "confidence_score": 0.92,
}


@pytest.mark.asyncio
async def test_analyze_video_success():
    """MiMo service correctly parses a valid analysis response."""
    service = MiMoService()
    
    with patch.object(service, "_call_mimo", return_value=json.dumps(VALID_ANALYSIS_JSON)):
        result = await service.analyze_video("https://example.com/video.mp4")
    
    assert result.scene_summary is not None
    assert len(result.style_options) == 3
    assert {opt.id for opt in result.style_options} == {"original", "cinematic", "documentary"}
    assert result.confidence_score == 0.92
    assert result.physical_properties.time_of_day == "Golden Hour"


@pytest.mark.asyncio
async def test_analyze_video_invalid_json():
    """MiMo service raises MiMoResponseParseError on invalid JSON."""
    service = MiMoService()

    with patch.object(service, "_call_mimo", return_value="not valid json"):
        with pytest.raises(MiMoResponseParseError):
            await service.analyze_video("https://example.com/video.mp4")


@pytest.mark.asyncio
async def test_analyze_video_missing_style_options():
    """MiMo service raises MiMoResponseParseError if style_options has wrong ids."""
    service = MiMoService()
    invalid_payload = dict(VALID_ANALYSIS_JSON)
    invalid_payload["style_options"] = [
        {**VALID_ANALYSIS_JSON["style_options"][0], "id": "wrong_id"},
        VALID_ANALYSIS_JSON["style_options"][1],
        VALID_ANALYSIS_JSON["style_options"][2],
    ]

    with patch.object(service, "_call_mimo", return_value=json.dumps(invalid_payload)):
        with pytest.raises(MiMoResponseParseError):
            await service.analyze_video("https://example.com/video.mp4")


@pytest.mark.asyncio
async def test_analyze_video_api_error():
    """MiMo service propagates HTTP errors correctly."""
    import httpx  # noqa: PLC0415

    service = MiMoService()

    with patch.object(
        service._client,
        "post",
        side_effect=httpx.TimeoutException("Connection timed out"),
    ):
        with pytest.raises(MiMoAPIError):
            await service.analyze_video("https://example.com/video.mp4")
