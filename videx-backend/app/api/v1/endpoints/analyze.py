"""
Analysis Endpoints.

GET /analyze/{job_id} — Get the Step 1 analysis result for a completed job
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.dependencies import CurrentUser, DbSession
from app.schemas.analysis import AnalysisResultResponse
from app.services.analysis_service import AnalysisService

router = APIRouter()


@router.get(
    "/{job_id}",
    response_model=AnalysisResultResponse,
    summary="Get analysis result for a completed job",
)
async def get_analysis_result(
    job_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> AnalysisResultResponse:
    """
    Retrieve the Step 1 MiMo V2.5 analysis result.

    The frontend should call this after receiving the 'analysis_complete' SSE event.
    Returns the full structured analysis including scene summary, physical properties,
    and 3 style options.
    """
    return await AnalysisService.get_analysis_result(db, job_id, current_user.id)
