import os

import anthropic
from anthropic.types import TextBlock

from app.inference.base import Model
from app.inference.types import ModelRequest, ModelResponse

_KEY = os.getenv("ANTHROPIC_API_KEY")


class Anthropic(Model):

    def __init__(self) -> None:
        if not _KEY:
            raise ValueError("Error: ANTHROPIC_API_KEY not assigned!")
        self.client = anthropic.AsyncAnthropic(api_key=_KEY)

    async def generate(self, request: ModelRequest) -> ModelResponse:

        response = await self.client.messages.create(
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens or 1024,
            system=request.system_prompt,
            messages=[{"role": "user", "content": request.user_prompt}],
        )

        text_parts = [
            block.text for block in response.content if isinstance(block, TextBlock)
        ]

        text = "\n".join(text_parts)

        return ModelResponse(
            raw_text=text,
            provider="anthropic",
            model=request.model,
        )
