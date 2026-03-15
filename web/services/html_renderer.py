"""Render CV replacements + CvTemplate → HTML string via Jinja2."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape

from web.schemas.cv_template_schema import CvTemplate

THEMES_DIR = Path(__file__).parent.parent / "html_themes"

_jinja_env = Environment(
    loader=FileSystemLoader(str(THEMES_DIR)),
    autoescape=select_autoescape(["html"]),
)


def render_cv_html(replacements: Dict[str, Any], template: CvTemplate) -> str:
    """Return a full HTML string for the given replacements and CvTemplate."""
    theme_file = f"{template.theme}.html.j2"
    try:
        jinja_template = _jinja_env.get_template(theme_file)
    except Exception:
        jinja_template = _jinja_env.get_template("classic.html.j2")

    # Sort sections by order, filter visible
    sections = sorted(
        [s for s in template.sections if s.visible],
        key=lambda s: s.order,
    )

    return jinja_template.render(
        replacements=replacements,
        sections=sections,
        page=template.page,
    )
