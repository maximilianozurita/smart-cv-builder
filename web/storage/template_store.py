"""Read/write CV templates as JSON files in web/cv_templates/."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from web.schemas.cv_template_schema import CvTemplate

TEMPLATES_DIR = Path(__file__).parent.parent / "cv_templates"
TEMPLATES_DIR.mkdir(exist_ok=True)


def _path(template_id: str) -> Path:
    return TEMPLATES_DIR / f"{template_id}.json"


def list_templates() -> List[dict]:
    results = []
    for f in sorted(f for f in TEMPLATES_DIR.glob("*.json") if not f.name.endswith(".example.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            results.append({"id": data.get("id", f.stem), "name": data.get("name", f.stem)})
        except Exception:
            pass
    return results


def get_template(template_id: str) -> Optional[CvTemplate]:
    p = _path(template_id)
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    return CvTemplate.model_validate(data)


def save_template(template: CvTemplate) -> CvTemplate:
    p = _path(template.id)
    p.write_text(template.model_dump_json(indent=2), encoding="utf-8")
    return template


def delete_template(template_id: str) -> bool:
    p = _path(template_id)
    if p.exists():
        p.unlink()
        return True
    return False
