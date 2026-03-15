"""FastAPI application — run from repo root with:
    uvicorn web.main:app --reload --port 8000
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from web.routers import ats, data_editor, export, generate, templates_router

app = FastAPI(title="smart-cv-builder", version="2.0.0")

# ── API Routers ───────────────────────────────────────────────────────────────
app.include_router(generate.router, prefix="/api")
app.include_router(templates_router.router, prefix="/api/templates")
app.include_router(export.router, prefix="/api/export")
app.include_router(ats.router, prefix="/api/ats")
app.include_router(data_editor.router, prefix="/api")

# ── Static files ──────────────────────────────────────────────────────────────
_static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/")
def root():
    return FileResponse(str(_static_dir / "index.html"))


# ── Utility: list available roles ─────────────────────────────────────────────
@app.get("/api/roles")
def list_roles():
    from config.settings import settings
    path = settings.data_dir / "roles.json"
    with path.open(encoding="utf-8") as f:
        roles = json.load(f)
    return [{"key": k, "label": v.get("display_name", k)} for k, v in roles.items()]
