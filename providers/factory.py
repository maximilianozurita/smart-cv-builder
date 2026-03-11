"""Factory: returns the appropriate provider instance."""
from __future__ import annotations

from config.settings import settings
from providers.base import BaseProvider


def get_provider(name: str) -> BaseProvider:
	name = name.lower().strip()

	if name == "openai":
		from providers.openai_provider import OpenAIProvider
		return OpenAIProvider(
			api_key=settings.api_key_for("openai"),
			model=settings.openai_model,
		)

	if name == "groq":
		from providers.groq_provider import GroqProvider
		return GroqProvider(
			api_key=settings.api_key_for("groq"),
			model=settings.groq_model,
		)

	if name == "anthropic":
		from providers.anthropic_provider import AnthropicProvider
		return AnthropicProvider(
			api_key=settings.api_key_for("anthropic"),
			model=settings.anthropic_model,
		)

	if name == "xai":
		from providers.xai_provider import XAIProvider
		return XAIProvider(
			api_key=settings.api_key_for("xai"),
			model=settings.xai_model,
		)

	if name == "gemini":
		from providers.gemini_provider import GeminiProvider
		return GeminiProvider(
			api_key=settings.api_key_for("gemini"),
			model=settings.gemini_model,
		)

	raise ValueError(
		f"Unknown provider '{name}'. Valid options: openai, groq, anthropic, xai, gemini."
	)
