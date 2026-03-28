from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SuccessEnvelope(BaseModel):
    success: bool = True
    data: dict[str, Any]
    trace_id: Optional[str] = None
    timestamp: str = Field(default_factory=utc_now_iso)


class ErrorEnvelope(BaseModel):
    success: bool = False
    error_code: str
    message: str
    trace_id: Optional[str] = None
    recoverable: bool = False
    timestamp: str = Field(default_factory=utc_now_iso)


class HealthResponse(SuccessEnvelope):
    data: dict[str, Any]
