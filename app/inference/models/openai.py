import os

from openai import AsyncOpenAI

from app.inference.base import Model
from app.inference.types import ModelRequest, ModelResponse

_KEY = os.getenv("OPENAI_API_KEY")


class OpenAI(Model):

    def __init__(self) -> None:
        if not _KEY:
            raise ValueError("Error: OPENAI_API_KEY not assigned!")
        self.client = AsyncOpenAI(api_key=_KEY)

    async def generate(self, request: ModelRequest) -> ModelResponse:

        response = await self.client.chat.completions.create(
            model=request.model,
            temperature=request.temperature,
            top_p=request.top_p,
            messages=[
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
            response_format={"type": "json_object"},
        )

        if not response.choices[0].message.content:
            raise ValueError("OpenAI response error!")

        return ModelResponse(
            raw_text=response.choices[0].message.content,
            provider="openai",
            model=request.model,
        )
