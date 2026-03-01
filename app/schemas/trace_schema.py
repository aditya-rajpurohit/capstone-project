from typing import Any

from pydantic import BaseModel, Field

from app.core.constants import EngineState


class ExecutionTraceRecord(BaseModel):
    user_query: str

    state: EngineState
    retry_count: int = 0

    plan: dict[str, Any] | None = None
    schema_context: dict[str, Any] | None = None
    generated_query: dict[str, Any] | None = None

    validation_result: dict[str, Any] | None = None
    execution_result: dict[str, Any] | None = None

    final_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    timestamp_iso: str
    prompt_hash: str | None = None
    response_hash: str | None = None
