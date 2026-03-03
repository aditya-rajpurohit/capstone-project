from typing import Any

from pydantic import BaseModel, Field

from app.core.constants import EngineState


class ExecutionTraceRecord(BaseModel):
    # -------------------------------------------------
    # 1️⃣ Input
    # -------------------------------------------------
    user_query: str
    timestamp_iso: str

    # -------------------------------------------------
    # 2️⃣ Workflow State
    # -------------------------------------------------
    state: EngineState
    retry_count: int = 0

    # -------------------------------------------------
    # 3️⃣ Agent Outputs
    # -------------------------------------------------
    plan: dict[str, Any] | None = None
    schema_context: dict[str, Any] | None = None
    generated_query: dict[str, Any] | None = None

    # -------------------------------------------------
    # 4️⃣ Critic + Validation
    # -------------------------------------------------
    critic_result: dict[str, Any] | None = None
    validation_result: dict[str, Any] | None = None

    # -------------------------------------------------
    # 5️⃣ Execution
    # -------------------------------------------------
    execution_result: dict[str, Any] | None = None
    execution_latency_ms: int | None = None

    # -------------------------------------------------
    # 6️⃣ Reflection
    # -------------------------------------------------
    reflection_history: list[dict[str, Any]] = Field(default_factory=list)

    # -------------------------------------------------
    # 7️⃣ Scoring
    # -------------------------------------------------
    final_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    risk_penalty: float | None = None
    critic_penalty: float | None = None
    retry_penalty: float | None = None
    final_score: float | None = None

    # -------------------------------------------------
    # 8️⃣ Optional Metadata
    # -------------------------------------------------
    prompt_hash: str | None = None
    response_hash: str | None = None
