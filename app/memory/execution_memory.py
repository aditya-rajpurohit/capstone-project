import uuid
from datetime import UTC, datetime
from typing import Any, Optional


class ExecutionMemory:
    def __init__(self, user_query: str, max_retries: int) -> None:
        # Core
        self.request_id: str = str(uuid.uuid4())
        self.user_query: str = user_query
        self.created_at: datetime = datetime.now(UTC)

        # State machine
        self.current_state: Optional[str] = None
        self.retry_count: int = 0
        self.max_retries: int = max_retries
        self.final_state: Optional[str] = None

        # Intelligence outputs
        self.planner_output: Optional[dict[str, Any]] = None
        self.filtered_schema: Optional[dict[str, Any]] = None
        self.generated_sql: Optional[str] = None
        self.critic_output: Optional[dict[str, Any]] = None
        self.validation_output: Optional[dict[str, Any]] = None

        # Execution
        self.execution_result: Optional[dict[str, Any]] = None
        self.execution_latency_ms: Optional[float] = None

        # Reflection
        self.reflection_history: list[dict[str, Any]] = []
        self.last_error_message: Optional[str] = None

        # Evaluation
        self.risk_penalty: float = 0.0
        self.critic_penalty: float = 0.0
        self.retry_penalty: float = 0.0
        self.final_score: Optional[float] = None
        self.confidence: Optional[float] = None
