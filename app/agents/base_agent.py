from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """
    Base interface for all reasoning agents.
    Agents return structured contract models.
    """

    @abstractmethod
    async def run(self, *args, **kwargs) -> Any:
        ...