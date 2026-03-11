"""Pydantic model for candidate_data.json."""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PersonalInfo(BaseModel):
	full_name: str
	location: str
	email: str
	phone: str
	linkedin: str


class Language(BaseModel):
	language: str
	level: str


class Education(BaseModel):
	institution: str
	degree: str
	end_date: str


class Experience(BaseModel):
	id: str
	company: str
	role: str
	start_date: str
	end_date: str
	description: str
	responsibilities: List[str] = Field(default_factory=list)
	technologies: List[str] = Field(default_factory=list)
	achievements: List[str] = Field(default_factory=list)


class CandidateData(BaseModel):
	personal_info: PersonalInfo
	languages: List[Language] = Field(default_factory=list)
	education: List[Education] = Field(default_factory=list)
	summary_base: str
	technical_skills: Dict[str, List[str]] = Field(default_factory=dict)
	experience: List[Experience] = Field(default_factory=list)
