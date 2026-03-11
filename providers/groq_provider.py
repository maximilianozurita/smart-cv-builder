"""Groq provider — uses the openai SDK with Groq's base URL."""
from __future__ import annotations

from openai import OpenAI

from providers.base import BaseProvider

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class GroqProvider(BaseProvider):
	def __init__(self, api_key: str, model: str) -> None:
		self._client = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)
		self._model = model

	def generate(self, system_prompt: str, user_prompt: str) -> str:
		response = self._client.chat.completions.create(
			model=self._model,
			messages=[
				{"role": "system", "content": system_prompt},
				{"role": "user", "content": user_prompt},
			],
			temperature=0.3,
		)
		return response.choices[0].message.content or ""
