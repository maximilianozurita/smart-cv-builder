"""POST /api/export/pdf  and  POST /api/export/docx"""
from __future__ import annotations

import asyncio
import io
import tempfile
from functools import partial
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import Response

from fastapi import APIRouter

from web.schemas.api_models import ExportRequest
from web.services import html_renderer, pdf_service

router = APIRouter()


@router.post("/pdf")
async def export_pdf(req: ExportRequest):
    html = html_renderer.render_cv_html(req.replacements, req.template)
    loop = asyncio.get_event_loop()
    try:
        pdf_bytes = await loop.run_in_executor(None, partial(pdf_service.html_to_pdf, html))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=cv.pdf"},
    )


@router.post("/docx")
async def export_docx(req: ExportRequest):
    from config.settings import settings
    from core.word_injector import inject

    template_path = settings.templates_dir / "cv_template.docx"
    if not template_path.exists():
        raise HTTPException(
            status_code=404,
            detail="cv_template.docx not found in templates/. DOCX export requires a Word template.",
        )

    loop = asyncio.get_event_loop()

    def _build_docx():
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            out_path = Path(tmp.name)
        inject(template_path, out_path, req.replacements)
        data = out_path.read_bytes()
        out_path.unlink(missing_ok=True)
        return data

    try:
        docx_bytes = await loop.run_in_executor(None, _build_docx)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DOCX generation failed: {e}")

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=cv.docx"},
    )
