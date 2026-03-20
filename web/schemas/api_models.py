"""Pydantic request/response models for the web API."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from web.schemas.cv_template_schema import CvTemplate


# ── Generate ──────────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    job_description: str
    role: str
    provider: str = "groq"
    dry_run: bool = False
    template_id: Optional[str] = "default"


class AtsScoreDetail(BaseModel):
    score: float  # 0-100
    matched_keywords: List[str]
    missing_keywords: List[str]
    section_scores: Dict[str, float]


class GenerateResponse(BaseModel):
    llm_response: Dict[str, Any]
    replacements: Dict[str, Any]
    preview_html: str
    ats_score: AtsScoreDetail
    cover_letter: str = ""


# ── Preview ───────────────────────────────────────────────────────────────────

class PreviewRequest(BaseModel):
    replacements: Dict[str, Any]
    template: CvTemplate


# ── ATS ───────────────────────────────────────────────────────────────────────

class AtsScoreRequest(BaseModel):
    job_description: str
    profile: str
    skills: str
    experience_bullets: List[str]


# ── Export ────────────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    replacements: Dict[str, Any]
    template: CvTemplate


# ── Cover Letter ──────────────────────────────────────────────────────────────

class CoverLetterRequest(BaseModel):
    job_description: str
    role: str
    provider: str = "groq"


class CoverLetterResponse(BaseModel):
    cover_letter: str
