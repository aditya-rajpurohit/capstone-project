from app.engine.agents.base_agents import BaseAgent
from app.engine.context.agent_context import AgentContext
from app.engine.inference.structured_model import StructuredModel
from app.engine.inference.types import ModelRequest
from app.engine.contracts.planner_contract import PlannerOutput


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
        user_prompt = f"User request:\n{context.user_query}"
        
        request = ModelRequest(
            system_prompt=PLANNER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=self.model_name,
            temperature=0.0,
        )

        return await self.model.generate(request, PlannerOutput)
