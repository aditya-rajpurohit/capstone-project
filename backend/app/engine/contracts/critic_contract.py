from typing import Literal, Optional

from pydantic import BaseModel, Field


class CriticOutput(BaseModel):
    logical_issues_detected: bool
    issue_summary: Optional[str] = None
    risk_level: Literal["low", "medium", "high"]
    confidence: float = Field(..., ge=0.0, le=1.0)
