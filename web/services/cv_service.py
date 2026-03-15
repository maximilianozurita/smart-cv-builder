"""Orchestrate the CV generation pipeline (async wrapper around existing sync code)."""
from __future__ import annotations

import asyncio
import json
from functools import partial
from pathlib import Path
from typing import Any, Dict

from config.settings import settings
from core.prompt_builder import build_prompt
from core.response_parser import ParseError, parse_and_validate
from providers.factory import get_provider
from schemas.candidate import CandidateData
from schemas.roles import RoleContext


# ── Data loading (sync, called via executor) ──────────────────────────────────

def _load_candidate() -> CandidateData:
    path = settings.data_dir / "candidate_data.json"
    with path.open(encoding="utf-8") as f:
        return CandidateData.model_validate(json.load(f))


def _load_roles() -> dict:
    path = settings.data_dir / "roles.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _load_role(role_key: str) -> RoleContext:
    roles = _load_roles()
    if role_key not in roles:
        raise ValueError(f"Role '{role_key}' not found. Available: {', '.join(roles)}")
    return RoleContext.model_validate(roles[role_key])


def load_candidate() -> CandidateData:
    return _load_candidate()


def load_roles() -> dict:
    return _load_roles()


# ── Mock response (for dry-run) ───────────────────────────────────────────────

def _mock_raw(candidate: CandidateData) -> str:
    exp = candidate.experience
    mock = {
        "profile": (
            "Backend engineer with experience designing REST APIs and microservices architectures. "
            "Proven track record optimizing performance in high-volume systems, leading technical teams, "
            "and delivering robust solutions in agile environments."
        ),
        "skills": "Python, SQL, REST APIs, Microservices | System Design, Technical Leadership, Agile/Scrum | Docker, PostgreSQL, Redis, AWS",
        "experiences": [
            {
                "company": exp[0].company if exp else "Company Alpha",
                "role": exp[0].role if exp else "Senior Backend Engineer",
                "start_date": exp[0].start_date if exp else "03/2022",
                "end_date": exp[0].end_date if exp else "Present",
                "bullets": [
                    "Design and implementation of REST APIs in Python/FastAPI consumed by 3 teams, reducing latency by 40%.",
                    "Leadership of legacy authentication system migration to OAuth 2.0 with zero downtime.",
                    "Increase of test coverage from 45% to 85% by establishing quality standards for the team.",
                ],
            },
            {
                "company": exp[1].company if len(exp) > 1 else "Company Beta",
                "role": exp[1].role if len(exp) > 1 else "Backend Developer",
                "start_date": exp[1].start_date if len(exp) > 1 else "06/2019",
                "end_date": exp[1].end_date if len(exp) > 1 else "02/2022",
                "bullets": [
                    "Processing of up to 5,000 transactions/hour integrating Stripe and PayPal with error rate <0.1%.",
                    "Reduction of batch report processing time from 4h to 45min by optimizing SQL queries.",
                    "Design of retry system that reduced payment failures by 25%.",
                ],
            },
        ],
    }
    return json.dumps(mock, ensure_ascii=False)


# ── Replacements builder ──────────────────────────────────────────────────────

def build_replacements(candidate: CandidateData, llm) -> Dict[str, Any]:
    pi = candidate.personal_info
    replacements: Dict[str, Any] = {
        "FULL_NAME": pi.full_name,
        "LOCATION": pi.location,
        "PHONE": pi.phone,
        "EMAIL": pi.email,
        "LINKEDIN": pi.linkedin,
        "LANGUAGES": ", ".join(f"{l.language} ({l.level})" for l in candidate.languages),
        "PROFILE": llm.profile,
        "SKILLS": _format_skills(llm.skills),
    }
    for i, edu in enumerate(candidate.education[:2], start=1):
        replacements[f"EDUCATION_INSTITUTION_{i}"] = edu.institution
        replacements[f"EDUCATION_DEGREE_{i}"] = edu.degree
        replacements[f"EDUCATION_END_DATE_{i}"] = edu.end_date
    for i, exp in enumerate(llm.experiences, start=1):
        replacements[f"EXPERIENCE_COMPANY_{i}"] = exp.company
        replacements[f"EXPERIENCE_ROLE_{i}"] = exp.role
        replacements[f"EXPERIENCE_START_DATE_{i}"] = exp.start_date
        replacements[f"EXPERIENCE_END_DATE_{i}"] = exp.end_date
        replacements[f"EXPERIENCE_DESCRIPTION_{i}"] = [f"• {b}" for b in exp.bullets]
    return replacements


def _format_skills(skills_str: str) -> list:
    groups = [g.strip() for g in skills_str.split("|") if g.strip()]
    return groups if groups else [skills_str]


# ── Main async pipeline ───────────────────────────────────────────────────────

async def run_pipeline(
    job_description: str,
    role_key: str,
    provider_name: str,
    dry_run: bool = False,
) -> dict:
    """
    Returns: {llm_response (dict), replacements (dict), llm_obj}
    Raises ValueError on bad role/provider, ParseError on bad LLM output.
    """
    loop = asyncio.get_event_loop()

    candidate = await loop.run_in_executor(None, _load_candidate)
    role = await loop.run_in_executor(None, partial(_load_role, role_key))

    system_prompt, user_prompt = build_prompt(candidate, role, job_description)

    if dry_run:
        raw = _mock_raw(candidate)
    else:
        def _call_llm():
            provider = get_provider(provider_name)
            return provider.generate(system_prompt, user_prompt)

        raw = await loop.run_in_executor(None, _call_llm)

    llm_obj = parse_and_validate(raw)
    replacements = build_replacements(candidate, llm_obj)

    return {
        "llm_response": llm_obj.model_dump(),
        "replacements": replacements,
        "llm_obj": llm_obj,
    }
