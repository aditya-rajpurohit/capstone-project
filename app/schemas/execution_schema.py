from typing import Any, Literal

from pydantic import BaseModel, Field


class ExecutionResult(BaseModel):
    status: Literal["success", "failed"]
    rows: list[dict[str, Any]] = Field(default_factory=lambda: [])
    row_count: int = 0
    elapsed_ms: int | None = None
    error_type: str | None = None
    error_message: str | None = None
