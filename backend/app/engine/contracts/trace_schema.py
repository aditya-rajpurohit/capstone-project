from typing import Any, Optional

from pydantic import BaseModel

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

    # Execution Result
    per_db_results: Optional[dict[str, dict[str, Any]]] = None
    synthesis_result: Optional[dict[str, Any]] = None
    execution_latency_ms: Optional[float] = None

    # Scoring
    final_confidence: Optional[float] = None
    risk_penalty: Optional[float] = None
    critic_penalty: Optional[float] = None
    retry_penalty: Optional[float] = None
    final_score: Optional[float] = None

    # Metadata
    prompt_hash: Optional[str] = None
    response_hash: Optional[str] = None
