from app.engine.agents.base_agents import BaseAgent
from app.engine.context.agent_context import AgentContext
from app.engine.inference.structured_model import StructuredModel
from app.engine.inference.types import ModelRequest
from app.engine.contracts.query_contract import QueryOutput
import json


QUERY_SYSTEM_PROMPT = """
    You are a SQL generation assistant.

    Rules:
    - Generate valid SQL SELECT query only.
    - Follow provided schema strictly.
    - Do not invent tables or columns.
    - Do not use SELECT *.
    - Always include LIMIT 100 unless otherwise specified.
    - Output strictly valid JSON.
"""


class QueryAgent(BaseAgent):

    def __init__(self, model: StructuredModel, model_name: str) -> None:
        self.model = model
        self.model_name = model_name

    async def run(self, context: AgentContext) -> QueryOutput:

        schema_str = json.dumps(context.filtered_schema, indent=2)
        plan_str = json.dumps(context.plan, indent=2)

        user_prompt = f"""
            User request:\n
            Plan: {plan_str}
            Schema: {schema_str}
        """

        if context.error_message:
            user_prompt += f"""
                User request:\n
                The previous SQL query failed with this error: {context.error_message}
                Generate a corrected SQL query.
            """

        request = ModelRequest(
            system_prompt=QUERY_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=self.model_name,
            temperature=0.0,
        )

        return await self.model.generate(request, QueryOutput)
