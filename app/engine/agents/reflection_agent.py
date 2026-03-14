from app.engine.agents.base_agent import BaseAgent
from app.engine.context.agent_context import AgentContext
from app.engine.inference.structured_model import StructuredModel
from app.engine.inference.types import ModelRequest
from app.engine.contracts.query_contract import QueryOutput


REFLECTION_SYSTEM_PROMPT = """
    You are a SQL generation assistant.

    Rules:
    - Generate valid SQL SELECT query only.
    - Follow provided schema strictly.
    - Do not invent tables or columns.
    - Do not use SELECT *.
    - Always include LIMIT 100 unless otherwise specified.
    - Output strictly valid JSON.
"""


class ReflectionAgent(BaseAgent):

    def __init__(self, model: StructuredModel, model_name: str) -> None:
        self.model = model
        self.model_name = model_name

    async def run(self, context: AgentContext) -> QueryOutput | str:

        user_prompt = f"""
            Plan: {context.plan}
            Schema: {context.filtered_schema}
            Previous SQL: {context.previous_sql}
            Error: {context.error_message}
            Generate a corrected SQL query.
        """

        request = ModelRequest(
            system_prompt=REFLECTION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=self.model_name,
            temperature=0.0,
        )

        return await self.model.generate(request, QueryOutput)
