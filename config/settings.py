"""Settings: loads .env and exposes typed configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from repo root
load_dotenv(Path(__file__).parent.parent / ".env")


@dataclass
class Settings:
	openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
	groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
	anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
	xai_api_key: str = field(default_factory=lambda: os.getenv("XAI_API_KEY", os.getenv("GROQ_API_KEY", "")))
	gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))

	openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))
	groq_model: str = field(default_factory=lambda: os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))
	xai_model: str = field(default_factory=lambda: os.getenv("XAI_MODEL", "grok-3-mini"))
	anthropic_model: str = field(
		default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
	)
	gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))

	# Paths
	data_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data")
	templates_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "templates")
	output_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "output")

	def api_key_for(self, provider: str) -> str:
		mapping = {
			"openai": self.openai_api_key,
			"groq": self.groq_api_key,
			"anthropic": self.anthropic_api_key,
			"xai": self.xai_api_key,
			"gemini": self.gemini_api_key,
		}
		key = mapping.get(provider, "")
		if not key:
			raise ValueError(
				f"API key for provider '{provider}' is not set. "
				f"Add it to your .env file (see .env.example)."
			)
		return key


# Singleton
settings = Settings()
