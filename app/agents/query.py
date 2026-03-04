from app.agents.base import BaseAgent
from app.context.agent_context import AgentContext
from app.inference.structured import StructuredModel
from app.inference.types import ModelRequest
from app.schemas.query_schema import QueryOutput

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

        user_prompt = f"""
            Plan: {context.plan}
            Schema: {context.filtered_schema}
        """

        if context.error_message:
            user_prompt += f"""
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
