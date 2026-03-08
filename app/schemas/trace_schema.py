from typing import Any, Optional

from pydantic import BaseModel, Field

from app.core.constants import EngineState


class ExecutionTraceRecord(BaseModel):

    # Request Metadata
    request_id: str
    user_query: str
    timestamp_iso: str

    # Final Outcome
    final_state: EngineState
    retry_count: int = 0

    # Intelligence Outputs
    plan: Optional[dict[str, Any]] = None
    filtered_schema: Optional[dict[str, Any]] = None
    generated_query: Optional[dict[str, Any]] = None

    # Critic + Validation
    critic_result: Optional[dict[str, Any]] = None
    validation_result: Optional[dict[str, Any]] = None

    # Execution Result
    per_db_results: Optional[dict[str, dict]] = None
    synthesis_result: Optional[dict[str, Any]] = None
    execution_latency_ms: Optional[float] = None

    # Reflection History
    reflection_history: list[dict[str, Any]] = Field(default_factory=list)

    # Scoring
    final_confidence: Optional[float] = None
    risk_penalty: Optional[float] = None
    critic_penalty: Optional[float] = None
    retry_penalty: Optional[float] = None
    final_score: Optional[float] = None

    # Optional Debug Metadata
    prompt_hash: Optional[str] = None
    response_hash: Optional[str] = None

