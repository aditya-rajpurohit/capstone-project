from typing import Any, Optional

from app.context.agent_context import AgentContext
from app.context.schema_selector import SchemaSelector
from app.memory.execution_memory import ExecutionMemory


class ContextBuilder:
    """
    Responsible for shaping ExecutionMemory into AgentContext.
    """

    @staticmethod
    def build_for_planner(memory: ExecutionMemory) -> AgentContext:
        return AgentContext(user_query=memory.user_query)

    @staticmethod
    def build_for_query(
        memory: ExecutionMemory,
        db_id: str,
        schema: dict[str, Any],
        preferred_tables: Optional[list[str]] = None,
    ) -> AgentContext:

        # Apply schema selector
        filtered = SchemaSelector.select(schema, memory.user_query)

        return AgentContext(
            user_query=memory.user_query,
            plan=memory.planner_output,
            filtered_schema=filtered,
            trace_hits=memory.trace_hits,
            schema_hits=memory.schema_hits,
        )

    @staticmethod
    def build_for_reflection(memory: ExecutionMemory, db_id: str) -> AgentContext:

        db_ctx = memory.per_db_context.get(db_id, {})

        last_error = db_ctx.get("last_error_message")
        previous_sql = db_ctx.get("generated_sql")

        return AgentContext(
            user_query=memory.user_query,
            plan=memory.planner_output,
            filtered_schema=db_ctx.get("schema"),
            previous_sql=previous_sql,
            error_message=last_error,
            trace_hits=memory.trace_hits,
            schema_hits=memory.schema_hits,
        )
