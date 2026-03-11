"""Anthropic provider using the official anthropic SDK."""
from __future__ import annotations

import anthropic

from providers.base import BaseProvider

MAX_TOKENS = 2048


class AnthropicProvider(BaseProvider):
	def __init__(self, api_key: str, model: str) -> None:
		self._client = anthropic.Anthropic(api_key=api_key)
		self._model = model

	def generate(self, system_prompt: str, user_prompt: str) -> str:
		message = self._client.messages.create(
			model=self._model,
			max_tokens=MAX_TOKENS,
			system=system_prompt,
			messages=[
				{"role": "user", "content": user_prompt},
			],
			temperature=0.3,
		)
		return message.content[0].text if message.content else ""
