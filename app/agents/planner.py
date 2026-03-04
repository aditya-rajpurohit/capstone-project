from app.agents.base import BaseAgent
from app.context.agent_context import AgentContext
from app.inference.structured import StructuredModel
from app.inference.types import ModelRequest
from app.schemas.planner_schema import PlannerOutput

PLANNER_SYSTEM_PROMPT = """
    You are a SQL planning assistant.

    You MUST output strictly valid JSON matching the schema.

    Rules:
    - "entities" must be a LIST.
    - "constraints" must be a LIST.
    - Always include "confidence" as a float between 0 and 1.
    - Do NOT return objects where lists are required.
    - Do NOT omit required fields.
    - Do NOT include extra keys.
    - Only SELECT operations are allowed.
"""


class PlannerAgent(BaseAgent):

    def __init__(self, model: StructuredModel, model_name: str) -> None:
        self.model = model
        self.model_name = model_name

    async def run(self, context: AgentContext) -> PlannerOutput:

        request = ModelRequest(
            system_prompt=PLANNER_SYSTEM_PROMPT,
            user_prompt=context.user_query,
            model=self.model_name,
            temperature=0.0,
        )

        return await self.model.generate(request, PlannerOutput)
