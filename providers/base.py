"""Abstract base class for all LLM providers."""
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseProvider(ABC):
	@abstractmethod
	def generate(self, system_prompt: str, user_prompt: str) -> str:
		"""Send prompts to the LLM and return the raw text response."""
		...
