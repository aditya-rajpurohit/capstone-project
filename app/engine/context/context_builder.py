from typing import Any, Optional

from app.engine.context.agent_context import AgentContext
from app.engine.context.schema_selector import SchemaSelector
from app.runtime.execution.execution_memory import ExecutionMemory


class ContextBuilder:
    """
    Responsible for shaping ExecutionMemory into AgentContext.
    """

    @staticmethod
    def build_for_planner(memory: ExecutionMemory) -> AgentContext:
        return AgentContext(user_query=memory.user_query)

    @staticmethod
    def build_for_query(
        memory: ExecutionMemory, db_id: str, schema: dict[str, Any]
    ) -> AgentContext:
        # Use schema hits to bias selection
        preferred_tables = [
            hit.metadata.get("table")
            for hit in memory.schema_hits
            if hit.metadata.get("data_source_id") == db_id and hit.metadata.get("table")
        ]

        # Apply schema selector
        filtered = SchemaSelector.select(
            schema, memory.user_query, preferred_tables=preferred_tables
        )

        return AgentContext(
            user_query=memory.user_query,
            plan=memory.planner_output,
            filtered_schema=filtered,
            trace_hits=memory.trace_hits,
            schema_hits=memory.schema_hits,
        )

    @staticmethod
    def build_for_reflection(memory: ExecutionMemory, db_id: str) -> AgentContext:

        db_context = memory.per_db_context.get(db_id, {})

        return AgentContext(
            user_query=memory.user_query,
            plan=memory.planner_output,
            filtered_schema=db_context.get("schema"),
            previous_sql=db_context.get("generated_sql"),
            error_message=db_context.get("last_error_message"),
            trace_hits=memory.trace_hits,
            schema_hits=memory.schema_hits,
        )
