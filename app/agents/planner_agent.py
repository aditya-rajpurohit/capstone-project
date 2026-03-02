from __future__ import annotations
from abc import abstractmethod
from app.agents.base_agent import BaseAgent
from app.schemas.planner_schema import PlannerOutput


class PlannerAgent(BaseAgent):

    @abstractmethod
    async def run(self, user_query: str) -> PlannerOutput:
        ...


class MockPlannerAgent(PlannerAgent):
    
    async def run(self, user_query: str) -> PlannerOutput:
        return PlannerOutput(
            intent="list",
            operation="SELECT",
            entities=[],
            constraints=[],
            confidence=1.0,
        )
