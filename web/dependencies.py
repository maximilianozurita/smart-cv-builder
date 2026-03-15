"""Shared FastAPI dependencies."""
from __future__ import annotations

import json
from pathlib import Path

from config.settings import settings
from schemas.candidate import CandidateData
from schemas.roles import RoleContext


def load_candidate() -> CandidateData:
    path = settings.data_dir / "candidate_data.json"
    with path.open(encoding="utf-8") as f:
        return CandidateData.model_validate(json.load(f))


def load_roles() -> dict:
    path = settings.data_dir / "roles.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)
