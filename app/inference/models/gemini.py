import os

from google import genai

from app.inference.base import Model
from app.inference.types import ModelRequest, ModelResponse

_KEY = os.getenv("GEMINI_API_KEY")


class Gemini(Model):

    def __init__(self) -> None:
        if not _KEY:
            raise ValueError("Error: GEMINI_API_KEY not assigned!")
        self.client = genai.Client(api_key=_KEY)

    async def generate(self, request: ModelRequest) -> ModelResponse:

        response = await self.client.aio.models.generate_content(
            model=request.model,
            contents=f"{request.system_prompt}\n\n{request.user_prompt}",
            config={
                "temperature": request.temperature,
                "top_p": request.top_p,
                "max_output_tokens": request.max_tokens or 1024,
            },
        )

        if response.text is None:
            raise ValueError("Gemini returned empty response.")

        return ModelResponse(
            raw_text=response.text,
            provider="gemini",
            model=request.model,
        )
