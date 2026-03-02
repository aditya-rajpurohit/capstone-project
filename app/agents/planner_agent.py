from app.agents.base_agent import BaseAgent
from app.inference.structured import StructuredModel
from app.inference.types import ModelRequest
from app.schemas.planner_schema import PlannerOutput

PLANNER_SYSTEM_PROMPT = """
You are a SQL planning assistant.

You must output strictly valid JSON that conforms to the schema.

Rules:
- Only SELECT operations are allowed.
- Extract intent clearly.
- Identify relevant entities and constraints.
- Do NOT generate SQL.
- Do NOT hallucinate tables.
"""


class PlannerAgent(BaseAgent):

    def __init__(self, model: StructuredModel, model_name: str) -> None:
        self.model = model
        self.model_name = model_name

    async def run(self, user_query: str) -> PlannerOutput:

        request = ModelRequest(
            system_prompt=PLANNER_SYSTEM_PROMPT,
            user_prompt=user_query,
            model=self.model_name,
            temperature=0.0,
        )

        return await self.model.generate(request, PlannerOutput)
