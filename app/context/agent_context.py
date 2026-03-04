from typing import Any, Optional


class AgentContext:
    """
    Structured input passed to agents.
    Prevents agents from directly depending on ExecutionMemory
    or raw orchestration state.
    """

    def __init__(
        self,
        user_query: str,
        plan: Optional[dict[str, Any]] = None,
        filtered_schema: Optional[dict[str, Any]] = None,
        previous_sql: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        self.user_query = user_query
        self.plan = plan
        self.filtered_schema = filtered_schema
        self.previous_sql = previous_sql
        self.error_message = error_message
