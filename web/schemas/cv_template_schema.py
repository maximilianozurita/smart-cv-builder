"""Pydantic models for CV template JSON structure."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


class PageConfig(BaseModel):
    margin_top_mm: float = 18.0
    margin_bottom_mm: float = 15.0
    margin_left_mm: float = 18.0
    margin_right_mm: float = 18.0
    font_family: str = "Inter"
    base_font_size_pt: float = 10.0
    accent_color: str = "#2563eb"
    title_color: str = "#1e3a8a"


class CvTemplateSection(BaseModel):
    id: str
    type: str  # header, text_block, skills_block, experience_block, education_block
    order: int
    visible: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)


class CvTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    theme: str = "classic"
    page: PageConfig = Field(default_factory=PageConfig)
    sections: List[CvTemplateSection] = Field(default_factory=list)
