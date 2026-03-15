"""POST /api/generate  and  POST /api/preview"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from core.response_parser import ParseError
from web.schemas.api_models import GenerateRequest, GenerateResponse, PreviewRequest
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
    )


@router.post("/preview")
async def preview(req: PreviewRequest):
    html = html_renderer.render_cv_html(req.replacements, req.template)
    return {"preview_html": html}
