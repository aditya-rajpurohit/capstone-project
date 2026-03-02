from abc import abstractmethod
from app.schemas.query_schema import QueryOutput
from app.schemas.planner_schema import PlannerOutput
from app.schemas.schema_context_schema import SchemaContext
from app.agents.base_agent import BaseAgent


class QueryAgent(BaseAgent):
    
    @abstractmethod
    async def run(self, plan: PlannerOutput, schema_context: SchemaContext) -> QueryOutput:
        ...


class MockQueryAgent(QueryAgent):
    
    async def run(self, plan: PlannerOutput, schema_context: SchemaContext) -> QueryOutput:

        # naive deterministic SQL for testing
        return QueryOutput(
            sql="SELECT * FROM users",
            explanation="Mock query",
            confidence=1.0,
        )
    