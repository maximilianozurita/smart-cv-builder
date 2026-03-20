"""Build the system and user prompts for the LLM."""
from __future__ import annotations

from schemas.candidate import CandidateData
from schemas.roles import RoleContext

OUTPUT_FORMAT = """\
Return ONLY a valid JSON object with this exact structure (no markdown, no explanation):
{
  "profile": "<summary paragraph, 50-400 chars, 3-4 lines max>",
  "skills": "<Group Label: skill1, skill2, skill3 | Group Label: skill1, skill2 | Group Label: skill1, skill2>",
  "experiences": [
	{
	  "company": "<company name>",
	  "role": "<job title>",
	  "start_date": "<MM/YYYY, e.g. 03/2022>",
	  "end_date": "<MM/YYYY, e.g. 12/2024, or 'Present'>",
	  "bullets": [
		"<action verb + context + metric>",
		"<action verb + context + metric>",
		"<action verb + context + metric>"
	  ]
	},
	{ ... second experience, same structure ... }
  ],
  "cover_letter": "<full cover letter, 3-4 paragraphs, first person, professional tone>"
}"""

SYSTEM_PROMPT_TEMPLATE = """\
You are an expert CV writer. Your task is to generate tailored CV content for a candidate.

STRICT RULES:
- Return ONLY valid JSON. No markdown, no code fences, no explanation text.
- Do NOT invent data, technologies, or achievements not present in the candidate's information.
- Select EXACTLY 2 experiences from the candidate's history, choosing those most relevant to the job description.
- Each experience must have between 1 and 8 bullets.
- Bullet format: noun-action phrase starting with the activity in noun/gerund form, then context and metric when available. Examples: "Development of REST APIs in FastAPI for payment platform.", "Optimization of SQL queries in PostgreSQL reducing latency by 40%.", "Automation of data pipelines with Airflow and AWS S3." — NO first person, NO past tense verbs as openers.
- For experiences NOT directly related to the target role, include only 1-2 bullets focused on transferable skills. Omit tasks irrelevant to the role.
- Within each experience, order bullets from most relevant to the target role first, down to least relevant.
- Date format: always MM/YYYY (e.g. 03/2019). Use "Present" if still active.
- Do NOT use first person (no "I", "my", "me").
- Write in the same language as the job description.
- The "profile" field must be 3-4 lines maximum (no more than 400 characters). Be concise and direct.
- The "skills" field: pipe-separated groups, each with a descriptive label followed by colon and comma-separated skills.
  Example: "Languages: Python, SQL, Java | Frameworks: FastAPI, Django | Cloud & DevOps: Docker, AWS, Kubernetes"
  Choose 3-5 groups with labels relevant to the job description. Each group on its own line when rendered.
- The "cover_letter" field: write a SHORT, direct cover letter — 2 paragraphs max, 5-6 sentences total.
  Sound like a real person, not a recruiter. No clichés ("I am writing to express", "I am excited about the opportunity", "Thank you for your consideration").
  First paragraph: why this specific role/company is interesting to the candidate, one concrete thing from their background that's directly relevant.
  Second paragraph: one or two specific achievements from their experience that match the JD, then a simple closing line.
  Use first person, casual-professional tone. No filler sentences. No corporate buzzwords.
  Do NOT invent achievements not present in the candidate's information.
  Write in the same language as the job description. Do not include subject line or headers — just the letter body.

{output_format}"""

USER_PROMPT_TEMPLATE = """\
## JOB DESCRIPTION
{job_description}

## ROLE CONTEXT
Role: {role_display_name}
Focus areas: {focus_areas}
Prioritize skills: {prioritize_skills}
Bullet style: {bullet_style}
Experience selection criteria: {experience_selection_criteria}

## CANDIDATE
Name: {candidate_name}

## CANDIDATE SKILLS
{skills_text}

## CANDIDATE SUMMARY BASE
{summary_base}

## CANDIDATE EXPERIENCE HISTORY
{experience_text}"""


def build_prompt(
	candidate: CandidateData,
	role: RoleContext,
	job_description: str,
) -> tuple[str, str]:
	"""Return (system_prompt, user_prompt)."""
	system_prompt = SYSTEM_PROMPT_TEMPLATE.format(output_format=OUTPUT_FORMAT)

	experience_text = _format_experiences(candidate)

	skills_text = "\n".join(
		f"{category.replace('_', ' ').title()}: {', '.join(items)}"
		for category, items in candidate.technical_skills.items()
	)

	user_prompt = USER_PROMPT_TEMPLATE.format(
		job_description=job_description.strip(),
		role_display_name=role.display_name,
		focus_areas=", ".join(role.focus_areas) or "general",
		prioritize_skills=", ".join(role.prioritize_skills) or "all",
		bullet_style=role.bullet_style,
		experience_selection_criteria=role.experience_selection_criteria or "most recent and relevant",
		candidate_name=candidate.personal_info.full_name,
		skills_text=skills_text,
		summary_base=candidate.summary_base,
		experience_text=experience_text,
	)

	return system_prompt, user_prompt


def _format_experiences(candidate: CandidateData) -> str:
	lines: list[str] = []
	for exp in candidate.experience:
		lines.append(f"[{exp.id}] {exp.company} — {exp.role}")
		lines.append(f"  Period: {exp.start_date} to {exp.end_date}")
		lines.append(f"  Description: {exp.description}")
		if exp.responsibilities:
			lines.append("  Responsibilities:")
			for r in exp.responsibilities:
				lines.append(f"    - {r}")
		if exp.technologies:
			lines.append(f"  Technologies: {', '.join(exp.technologies)}")
		if exp.achievements:
			lines.append("  Achievements:")
			for a in exp.achievements:
				lines.append(f"    - {a}")
		lines.append("")
	return "\n".join(lines)
