from abc import ABC, abstractmethod
from typing import Any

from app.context.agent_context import AgentContext


class BaseAgent(ABC):
    """
    All intelligence agents must:
    - Accept AgentContext
    - Return structured output
    - Be stateless
    """

    @abstractmethod
    async def run(self, context: AgentContext) -> Any:
        pass
