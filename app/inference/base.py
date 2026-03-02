from abc import ABC, abstractmethod

from app.inference.types import ModelRequest, ModelResponse


class Model(ABC):
    """
    Abstract model interface.
    Concrete implementations: OpenAI, Anthropic, Gemini...
    """

    @abstractmethod
    async def generate(self, request: ModelRequest) -> ModelResponse: ...
