from abc import abstractmethod

from app.schemas.planner_schema import PlannerOutput
from app.schemas.query_schema import QueryOutput
from app.schemas.schema_context_schema import SchemaContext

from .base_agent import BaseAgent


class ReflectionAgent(BaseAgent):

    async def run(
        self,
        plan: PlannerOutput,
        schema_context: SchemaContext,
        previous_sql: str,
        error_message: str,
    ) -> QueryOutput: ...


class TestReflectionAgent:

    def __init__(self):
        self.call_count = 0

    async def run(
        self, plan, schema_context, previous_sql, error_message
    ) -> QueryOutput:
        self.call_count += 1

        # Always fix wrong column
        return QueryOutput(
            sql="SELECT name FROM users ORDER BY id",
            explanation="Corrected query",
            confidence=0.9,
        )
