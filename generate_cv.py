#!/usr/bin/env python3
"""
cvAutomat — CLI entrypoint.

Usage:
	python generate_cv.py --role backend_engineer --jd job_description.txt --provider groq
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from config.settings import settings
from core.prompt_builder import build_prompt
from core.response_parser import ParseError, parse_and_validate
from core.word_injector import inject
from providers.factory import get_provider
from schemas.candidate import CandidateData
from schemas.roles import RoleContext


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Generate a tailored CV using an LLM.",
	)
	parser.add_argument(
		"--role",
		required=True,
		help="Role key from data/roles.json (e.g. backend_engineer).",
	)
	parser.add_argument(
		"--jd",
		required=True,
		type=Path,
		help="Path to a plain-text job description file.",
	)
	parser.add_argument(
		"--provider",
		required=True,
		choices=["groq", "openai", "anthropic", "xai", "gemini"],
		help="LLM provider to use.",
	)
	parser.add_argument(
		"--template",
		type=Path,
		default=None,
		help="Override path to the .docx template (default: templates/cv_template.docx).",
	)
	parser.add_argument(
		"--output",
		type=Path,
		default=None,
		help="Override output path (default: output/Zurita_Maximiliano.docx).",
	)
	parser.add_argument(
		"--dry-run",
		action="store_true",
		help="Skip LLM call; use a mock response to test the full pipeline.",
	)
	return parser.parse_args()


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_candidate() -> CandidateData:
	path = settings.data_dir / "candidate_data.json"
	if not path.exists():
		_fatal(f"Candidate data not found: {path}")
	with path.open(encoding="utf-8") as f:
		return CandidateData.model_validate(json.load(f))


def load_role(role_key: str) -> RoleContext:
	path = settings.data_dir / "roles.json"
	if not path.exists():
		_fatal(f"Roles file not found: {path}")
	with path.open(encoding="utf-8") as f:
		roles: dict = json.load(f)
	if role_key not in roles:
		available = ", ".join(roles.keys())
		_fatal(f"Role '{role_key}' not found. Available: {available}")
	return RoleContext.model_validate(roles[role_key])


def load_jd(path: Path) -> str:
	if not path.exists():
		_fatal(f"Job description file not found: {path}")
	return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Placeholder building
# ---------------------------------------------------------------------------

def build_replacements(candidate: CandidateData, llm: "LLMResponse") -> dict:  # type: ignore[name-defined]
	pi = candidate.personal_info

	replacements: dict = {
		"FULL_NAME": pi.full_name,
		"LOCATION": pi.location,
		"PHONE": pi.phone,
		"EMAIL": pi.email,
		"LINKEDIN": pi.linkedin,
		"LANGUAGES": ", ".join(
			f"{lang.language} ({lang.level})" for lang in candidate.languages
		),
		"PROFILE": llm.profile,
		"SKILLS": _format_skills(llm.skills),
	}

	# Education (up to 2)
	for i, edu in enumerate(candidate.education[:2], start=1):
		replacements[f"EDUCATION_INSTITUTION_{i}"] = edu.institution
		replacements[f"EDUCATION_DEGREE_{i}"] = edu.degree
		replacements[f"EDUCATION_END_DATE_{i}"] = edu.end_date

	# Experiences (always 2 from LLM)
	for i, exp in enumerate(llm.experiences, start=1):
		replacements[f"EXPERIENCE_COMPANY_{i}"] = exp.company
		replacements[f"EXPERIENCE_ROLE_{i}"] = exp.role
		replacements[f"EXPERIENCE_START_DATE_{i}"] = exp.start_date
		replacements[f"EXPERIENCE_END_DATE_{i}"] = exp.end_date
		replacements[f"EXPERIENCE_DESCRIPTION_{i}"] = [f"• {b}" for b in exp.bullets]

	return replacements


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
	args = parse_args()

	print(f"[cvAutomat] Loading candidate data...")
	candidate = load_candidate()

	print(f"[cvAutomat] Loading role: {args.role}")
	role = load_role(args.role)

	print(f"[cvAutomat] Loading job description: {args.jd}")
	job_description = load_jd(args.jd)

	print(f"[cvAutomat] Building prompts...")
	system_prompt, user_prompt = build_prompt(candidate, role, job_description)

	if args.dry_run:
		print(f"[cvAutomat] DRY RUN — skipping LLM call, using mock response.")
		raw_response = _mock_llm_response(candidate)
	else:
		print(f"[cvAutomat] Calling provider: {args.provider}...")
		try:
			provider = get_provider(args.provider)
			raw_response = provider.generate(system_prompt, user_prompt)
		except ValueError as e:
			_fatal(str(e))
		except Exception as e:
			_fatal(f"Provider '{args.provider}' error: {e}")

	print(f"[cvAutomat] Parsing and validating LLM response...")
	try:
		llm_response = parse_and_validate(raw_response)
	except ParseError as e:
		_fatal(str(e))

	print(f"[cvAutomat] Building replacements...")
	replacements = build_replacements(candidate, llm_response)

	template_path = args.template or (settings.templates_dir / "cv_template.docx")
	if not template_path.exists():
		_fatal(f"Template not found: {template_path}")

	name_snake = candidate.personal_info.full_name.lower().replace(" ", "_")

	if args.output:
		output_path = args.output
	else:
		output_path = settings.output_dir / f"{name_snake}.docx"

	print(f"[cvAutomat] Injecting into template: {template_path}")
	inject(template_path, output_path, replacements)
	print(f"[cvAutomat] Word saved: {output_path}")

	pdf_path = output_path.with_suffix(".pdf")
	print(f"[cvAutomat] Converting to PDF...")
	try:
		_convert_to_pdf_macos(output_path, pdf_path)
		print(f"[cvAutomat] PDF saved:  {pdf_path}")
	except Exception as e:
		print(f"[WARNING] PDF conversion failed: {e}")

	print(f"\n[cvAutomat] Done!")


def _convert_to_pdf_macos(docx_path, pdf_path):
	import subprocess, shutil
	docx_abs = str(docx_path.resolve())
	out_dir = str(pdf_path.resolve().parent)

	# Try LibreOffice (free, reliable headless conversion)
	soffice = shutil.which("soffice") or "/Applications/LibreOffice.app/Contents/MacOS/soffice"
	if shutil.which("soffice") or __import__("os").path.exists(soffice):
		result = subprocess.run(
			[soffice, "--headless", "--convert-to", "pdf", "--outdir", out_dir, docx_abs],
			capture_output=True, text=True
		)
		if result.returncode == 0:
			# soffice names the output <stem>.pdf in outdir; rename if needed
			generated = pdf_path.parent / (docx_path.stem + ".pdf")
			if generated != pdf_path and generated.exists():
				generated.rename(pdf_path)
			return
		raise RuntimeError(result.stderr.strip() or result.stdout.strip())

	raise RuntimeError(
		"LibreOffice not found. Install it with: brew install --cask libreoffice"
	)


def _format_skills(skills_str: str) -> list:
	"""Split 'Group: a, b | Group: c, d' into one string per group."""
	groups = [g.strip() for g in skills_str.split("|") if g.strip()]
	return groups if groups else [skills_str]


def _mock_llm_response(candidate: CandidateData) -> str:
	import json as _json
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
					"Reduction of batch report processing time from 4 h to 45 min by optimizing SQL queries.",
					"Design of retry system that reduced payment failures by 25%.",
				],
			},
		],
	}
	return _json.dumps(mock, ensure_ascii=False)


def _fatal(msg: str) -> None:
	print(f"[ERROR] {msg}", file=sys.stderr)
	sys.exit(1)


if __name__ == "__main__":
	main()
