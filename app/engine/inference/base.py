from abc import ABC, abstractmethod
from typing import Optional, Type

from pydantic import BaseModel

from app.engine.inference.types import ModelRequest, ModelResponse


class Model(ABC):
    """
    Abstract model interface.
    Concrete implementations: OpenAI, Anthropic, Gemini...
    """

    @abstractmethod
    async def generate(
        self, request: ModelRequest, schema: Optional[Type[BaseModel]] = None
    ) -> ModelResponse: ...
