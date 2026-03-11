"""Parse and validate raw LLM text into LLMResponse."""
from __future__ import annotations

import json
import re

from schemas.llm_response import LLMResponse

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


class ParseError(Exception):
	"""Raised when the LLM response cannot be parsed or validated."""


def parse_and_validate(raw: str) -> LLMResponse:
	"""
	3-layer parsing strategy:
	1. Strip markdown fences.
	2. json.loads() directly.
	3. Regex fallback to extract first {...} block.
	Raises ParseError with diagnostic info on failure.
	"""
	cleaned = _strip_fences(raw)

	data = _try_json_loads(cleaned)
	if data is None:
		data = _try_regex_extract(raw)

	if data is None:
		snippet = raw[:500]
		raise ParseError(
			f"Could not parse JSON from LLM response.\n"
			f"First 500 chars:\n{snippet}"
		)

	try:
		return LLMResponse.model_validate(data)
	except Exception as exc:
		snippet = raw[:500]
		raise ParseError(
			f"LLM response parsed as JSON but failed Pydantic validation: {exc}\n"
			f"First 500 chars:\n{snippet}"
		) from exc


def _strip_fences(text: str) -> str:
	match = _FENCE_RE.search(text)
	if match:
		return match.group(1)
	return text.strip()


def _try_json_loads(text: str) -> dict | None:
	try:
		result = json.loads(text)
		if isinstance(result, dict):
			return result
	except json.JSONDecodeError:
		pass
	return None


def _try_regex_extract(text: str) -> dict | None:
	match = _JSON_OBJECT_RE.search(text)
	if match:
		return _try_json_loads(match.group(0))
	return None
