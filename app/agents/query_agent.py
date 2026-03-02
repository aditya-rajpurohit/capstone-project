from app.agents.base_agent import BaseAgent
from app.inference.structured import StructuredModel
from app.inference.types import ModelRequest
from app.schemas.planner_schema import PlannerOutput
from app.schemas.query_schema import QueryOutput
from app.schemas.schema_context_schema import SchemaContext

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

    async def run(
        self,
        plan: PlannerOutput,
        schema_context: SchemaContext,
        error_feedback: str | None = None,
    ) -> QueryOutput:

        user_prompt = f"""
            Plan: {plan.model_dump_json(indent=2)}
            Schema: {schema_context.model_dump_json(indent=2)}
        """

        if error_feedback:
            user_prompt += f"""
                The previous SQL query failed with this error: {error_feedback}
                Generate a corrected SQL query.
            """

        request = ModelRequest(
            system_prompt=QUERY_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=self.model_name,
            temperature=0.0,
        )

        return await self.model.generate(request, QueryOutput)
