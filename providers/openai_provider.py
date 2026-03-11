"""OpenAI provider using the official openai SDK."""
from __future__ import annotations

from openai import OpenAI

from providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
	def __init__(self, api_key: str, model: str) -> None:
		self._client = OpenAI(api_key=api_key)
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
