from app.engine.agents.base_agents import BaseAgent
from app.engine.context.agent_context import AgentContext
from app.engine.inference.structured_model import StructuredModel
from app.engine.inference.types import ModelRequest
from app.engine.contracts.critic_contract import CriticOutput
import json


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

        previous_sql_str = json.dumps(context.previous_sql, indent=2)
        schema_str = json.dumps(context.filtered_schema, indent=2)

        user_prompt = f"""
            User request:\n
            SQL: {previous_sql_str}
            Schema: {schema_str}
        """

        request = ModelRequest(
            system_prompt=CRITIC_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=self.model_name,
            temperature=0.0,
        )

        return await self.model.generate(request, CriticOutput)
