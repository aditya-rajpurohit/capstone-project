from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ExecutionResult(BaseModel):
    status: Literal["success", "failed"]
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = Field(default=0, ge=0)
    elapsed_ms: Optional[int] = Field(default=None, ge=0)
    error_type: Optional[str] = None
    error_message: Optional[str] = None
