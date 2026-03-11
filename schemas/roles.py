"""Pydantic model for roles.json."""
from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field


class RoleContext(BaseModel):
	display_name: str
	focus_areas: List[str] = Field(default_factory=list)
	prioritize_skills: List[str] = Field(default_factory=list)
	bullet_style: str = "action + context + metric"
	experience_selection_criteria: str = ""
