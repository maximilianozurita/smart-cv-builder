"""Pydantic model for LLM response validation."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, field_validator


class ExperienceLLM(BaseModel):
	company: str
	role: str
	start_date: str
	end_date: str
	bullets: List[str] = Field(min_length=1, max_length=6)

	@field_validator("bullets")
	@classmethod
	def bullets_not_empty(cls, v: List[str]) -> List[str]:
		for b in v:
			if not b.strip():
				raise ValueError("Bullet cannot be empty.")
		return v


class LLMResponse(BaseModel):
	profile: str = Field(min_length=50, max_length=800)
	skills: str = Field(min_length=5)
	experiences: List[ExperienceLLM] = Field(min_length=2, max_length=2)

	@field_validator("experiences")
	@classmethod
	def exactly_two_experiences(cls, v: List[ExperienceLLM]) -> List[ExperienceLLM]:
		if len(v) != 2:
			raise ValueError(f"Expected exactly 2 experiences, got {len(v)}.")
		return v
