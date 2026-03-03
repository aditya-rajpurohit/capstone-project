from app.agents.base_agent import BaseAgent
from app.inference.structured import StructuredModel
from app.inference.types import ModelRequest
from app.schemas.critic_schema import CriticOutput
from app.schemas.query_schema import QueryOutput
from app.schemas.schema_context_schema import SchemaContext

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

    async def run(
        self,
        query_output: QueryOutput,
        schema_context: SchemaContext,
    ) -> CriticOutput:

        request = ModelRequest(
            system_prompt=CRITIC_SYSTEM_PROMPT,
            user_prompt=f"""
                SQL: {query_output.sql}
                Schema: {schema_context.model_dump_json(indent=2)}
            """,
            model=self.model_name,
            temperature=0.0,
        )

        return await self.model.generate(request, CriticOutput)
