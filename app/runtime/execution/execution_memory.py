import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.constants import EngineState
from app.retrieval.retrieval_types import RetrievalHit


class ExecutionMemory:
    """
    Request-scoped runtime memory.

    - Lives for a single controller.run() call
    - Owns execution state
    - Not persisted directly (trace is derived from this)
    """

    def __init__(
        self,
        user_query: str,
        active_database_ids: list[str],
        max_retries: int,
    ) -> None:

        # ---- Core ----
        self.request_id: str = str(uuid.uuid4())
        self.user_query: str = user_query
        self.created_at: datetime = datetime.now(timezone.utc)

        self.active_database_ids: list[str] = active_database_ids

        # ---- State Machine ----
        self.current_state: Optional[EngineState] = None
        self.final_state: Optional[EngineState] = None

        self.max_retries: int = max_retries

        # ---- Global Intelligence Outputs ----
        self.planner_output: Optional[dict[str, Any]] = None
        self.final_confidence: Optional[float] = None

        # ---- Retrieval (Layer 2) ----
        self.schema_hits: list[RetrievalHit] = []
        self.trace_hits: list[RetrievalHit] = []

        # ---- Per-DB Execution Context ----
        # db_id -> {
        #   "schema": dict,
        #   "generated_sql": str,
        #   "validation": dict,
        #   "execution_result": dict,
        #   "retry_count": int,
        #   "reflection_history": list[dict],
        # }
        self.per_db_context: dict[str, dict[str, Any]] = {}

        # ---- Synthesis ----
        self.synthesis_result: Optional[dict[str, Any]] = None

        # ---- Evaluation ----
        self.risk_penalty: float = 0.0
        self.critic_penalty: float = 0.0
        self.retry_penalty: float = 0.0
        self.final_score: Optional[float] = None

    # ---------------------------------------
    # Utility helpers
    # ---------------------------------------

    def init_db_context(self, db_id: str) -> None:
        """
        Initialize per-DB execution container.
        """
        self.per_db_context[db_id] = {
            "retry_count": 0,
            "reflection_history": [],
        }

    def increment_retry(self, db_id: str) -> None:
        self.per_db_context[db_id]["retry_count"] += 1

    def add_reflection(self, db_id: str, previous_sql: str, error_message: str) -> None:
        self.per_db_context[db_id]["reflection_history"].append(
            {
                "previous_sql": previous_sql,
                "error_message": error_message,
            }
        )

    def total_retry_count(self) -> int:
        return sum(ctx.get("retry_count", 0) for ctx in self.per_db_context.values())

    def set_db_error(self, db_id: str, message: str) -> None:
        self.per_db_context.setdefault(db_id, {})
        self.per_db_context[db_id]["last_error_message"] = message
