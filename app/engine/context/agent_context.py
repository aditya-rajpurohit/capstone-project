from dataclasses import dataclass
from typing import Any, Optional

from app.retrieval.retrieval_types import RetrievalHit


@dataclass
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
        trace_hits: Optional[list[RetrievalHit]] = None,
        schema_hits: Optional[list[RetrievalHit]] = None,
    ) -> None:
        self.user_query = user_query
        self.plan = plan
        self.filtered_schema = filtered_schema
        self.previous_sql = previous_sql
        self.error_message = error_message
        self.trace_hits = trace_hits or []
        self.schema_hits = schema_hits or []
