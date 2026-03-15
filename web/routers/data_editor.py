"""Routes for editing candidate data, roles, and uploading the Word template."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, UploadFile, File

router = APIRouter()

_ROOT = Path(__file__).parent.parent.parent  # project root
_CANDIDATE_FILE = _ROOT / "data" / "candidate_data.json"
_ROLES_FILE = _ROOT / "data" / "roles.json"
_DOCX_TEMPLATE = _ROOT / "templates" / "cv_template.docx"


@router.get("/candidate-data")
def get_candidate_data():
    try:
        return json.loads(_CANDIDATE_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise HTTPException(404, "candidate_data.json not found")


@router.put("/candidate-data")
async def save_candidate_data(request: Request):
    try:
        data = await request.json()
        _CANDIDATE_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return {"ok": True}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/roles-data")
def get_roles_data():
    try:
        return json.loads(_ROLES_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise HTTPException(404, "roles.json not found")


@router.put("/roles-data")
async def save_roles_data(request: Request):
    try:
        data = await request.json()
        _ROLES_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return {"ok": True}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/docx-template/info")
def get_docx_template_info():
    if not _DOCX_TEMPLATE.exists():
        return {"exists": False, "name": None, "size_kb": None}
    stat = _DOCX_TEMPLATE.stat()
    return {
        "exists": True,
        "name": _DOCX_TEMPLATE.name,
        "size_kb": round(stat.st_size / 1024, 1),
    }


@router.post("/docx-template")
async def upload_docx_template(file: UploadFile = File(...)):
    if not (file.filename or "").endswith(".docx"):
        raise HTTPException(400, "Only .docx files are accepted")
    content = await file.read()
    _DOCX_TEMPLATE.parent.mkdir(parents=True, exist_ok=True)
    _DOCX_TEMPLATE.write_bytes(content)
    return {"ok": True, "name": file.filename, "size_kb": round(len(content) / 1024, 1)}
