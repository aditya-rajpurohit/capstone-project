from app.agents.base import BaseAgent
from app.context.agent_context import AgentContext
from app.inference.structured import StructuredModel
from app.inference.types import ModelRequest
from app.schemas.critic_schema import CriticOutput

CRITIC_SYSTEM_PROMPT = """
    You are a SQL review assistant.

    Analyze the SQL query for:
    - Logical join mistakes
    - Missing filters
    - Suspicious SELECT *
    - Aggregation errors

    Return structured JSON only.
"""


class CriticAgent(BaseAgent):

    def __init__(self, model: StructuredModel, model_name: str) -> None:
        self.model = model
        self.model_name = model_name

    async def run(self, context: AgentContext) -> CriticOutput:

        request = ModelRequest(
            system_prompt=CRITIC_SYSTEM_PROMPT,
            user_prompt=f"""
                SQL: {context.previous_sql}
                Schema: {context.filtered_schema}
            """,
            model=self.model_name,
            temperature=0.0,
        )

        return await self.model.generate(request, CriticOutput)
