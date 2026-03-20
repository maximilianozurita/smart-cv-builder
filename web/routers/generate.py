"""POST /api/generate  and  POST /api/preview"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException

from core.response_parser import ParseError
from providers.factory import get_provider
from web.schemas.api_models import CoverLetterRequest, CoverLetterResponse, GenerateRequest, GenerateResponse, PreviewRequest
from web.schemas.cv_template_schema import CvTemplate
from web.services import ats_service, cv_service, html_renderer
from web.storage import template_store

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    # Load template
    tmpl_id = req.template_id or "default"
    template = template_store.get_template(tmpl_id)
    if template is None:
        template = template_store.get_template("default")
    if template is None:
        template = CvTemplate(id="default", name="Default")

    # Run pipeline
    try:
        result = await cv_service.run_pipeline(
            job_description=req.job_description,
            role_key=req.role,
            provider_name=req.provider,
            dry_run=req.dry_run,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ParseError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    replacements = result["replacements"]
    llm_obj = result["llm_obj"]

    # Render HTML preview
    preview_html = html_renderer.render_cv_html(replacements, template)

    # ATS score
    bullets = []
    for exp in llm_obj.experiences:
        bullets.extend(exp.bullets)
    ats_data = ats_service.score_ats(
        job_description=req.job_description,
        profile=llm_obj.profile,
        skills=llm_obj.skills,
        experience_bullets=bullets,
    )

    return GenerateResponse(
        llm_response=result["llm_response"],
        replacements=replacements,
        preview_html=preview_html,
        ats_score=ats_data,
        cover_letter=llm_obj.cover_letter,
    )


@router.post("/preview")
async def preview(req: PreviewRequest):
    html = html_renderer.render_cv_html(req.replacements, req.template)
    return {"preview_html": html}


@router.post("/cover-letter", response_model=CoverLetterResponse)
async def generate_cover_letter(req: CoverLetterRequest):
    candidate = cv_service.load_candidate()
    pi = candidate.personal_info

    name = pi.full_name
    skills_summary = ", ".join(
        exp.role for exp in candidate.experience[:2]
    ) if candidate.experience else req.role

    system_prompt = (
        "You are an expert cover letter writer. "
        "Write professional, concise, and personalized cover letters tailored to the job description. "
        "Return only the cover letter text — no subject line, no headers, no extra commentary."
    )
    user_prompt = (
        f"Write a cover letter for {name} applying for the role of {req.role}.\n\n"
        f"Job Description:\n{req.job_description}\n\n"
        f"Candidate background: {skills_summary}.\n\n"
        f"Keep it to 3-4 short paragraphs. Be specific and enthusiastic. "
        f"End with a professional closing."
    )

    loop = asyncio.get_event_loop()

    def _call():
        provider = get_provider(req.provider)
        return provider.generate(system_prompt, user_prompt)

    try:
        cover_letter = await loop.run_in_executor(None, _call)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return CoverLetterResponse(cover_letter=cover_letter)
