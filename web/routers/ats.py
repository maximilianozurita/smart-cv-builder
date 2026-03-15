"""POST /api/ats/score"""
from __future__ import annotations

from fastapi import APIRouter

from web.schemas.api_models import AtsScoreRequest
from web.services import ats_service

router = APIRouter()


@router.post("/score")
def ats_score(req: AtsScoreRequest):
    return ats_service.score_ats(
        job_description=req.job_description,
        profile=req.profile,
        skills=req.skills,
        experience_bullets=req.experience_bullets,
    )
