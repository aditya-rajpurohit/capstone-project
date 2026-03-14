from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from app.engine.context.agent_context import AgentContext

T = TypeVar("T")

class BaseAgent(ABC, Generic[T]):
    """
    All intelligence agents:
    - Accept AgentContext
    - Return structured contract
    - Are stateless
    """

    @abstractmethod
    async def run(self, context: AgentContext) -> T:
        ...
