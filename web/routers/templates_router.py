"""CRUD /api/templates"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from web.schemas.cv_template_schema import CvTemplate
from web.storage import template_store

router = APIRouter()


@router.get("")
def list_templates():
    return template_store.list_templates()


@router.get("/{template_id}")
def get_template(template_id: str):
    tmpl = template_store.get_template(template_id)
    if tmpl is None:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found.")
    return tmpl


@router.post("")
def create_template(template: CvTemplate):
    return template_store.save_template(template)


@router.put("/{template_id}")
def update_template(template_id: str, template: CvTemplate):
    template.id = template_id
    return template_store.save_template(template)


@router.delete("/{template_id}")
def delete_template(template_id: str):
    ok = template_store.delete_template(template_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found.")
    return {"deleted": template_id}
