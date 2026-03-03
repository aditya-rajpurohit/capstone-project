from abc import ABC, abstractmethod
from typing import Type

from pydantic import BaseModel

from app.inference.types import ModelRequest, ModelResponse


class Model(ABC):
    """
    Abstract model interface.
    Concrete implementations: OpenAI, Anthropic, Gemini...
    """

    @abstractmethod
    async def generate(
        self,
        request: ModelRequest,
        schema: Type[BaseModel] | None = None,
    ) -> ModelResponse: ...
