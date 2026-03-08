from app.context.agent_context import AgentContext
from app.context.schema_selector import SchemaSelector
from app.memory.execution_memory import ExecutionMemory


class ContextBuilder:
    """
    Responsible for shaping ExecutionMemory into AgentContext.
    Centralizes context engineering.
    """

    @staticmethod
    def build_for_planner(memory: ExecutionMemory) -> AgentContext:
        return AgentContext(
            user_query=memory.user_query,
        )

    @staticmethod
    def build_for_query(memory: ExecutionMemory, schema: dict) -> AgentContext:
        filtered = SchemaSelector.select(schema, memory.user_query)

        return AgentContext(
            user_query=memory.user_query,
            plan=memory.planner_output,
            filtered_schema=filtered,
        )

    @staticmethod
    def build_for_reflection(memory: ExecutionMemory) -> AgentContext:
        last_error = memory.last_error_message
        previous_sql = memory.generated_sql

        return AgentContext(
            user_query=memory.user_query,
            plan=memory.planner_output,
            filtered_schema=memory.filtered_schema,
            previous_sql=previous_sql,
            error_message=last_error,
        )
