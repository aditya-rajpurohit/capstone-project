from typing import List, Literal

from pydantic import BaseModel, Field


class RuleFinding(BaseModel):
    rule_id: str
    severity: Literal["low", "medium", "high"]
    message: str


class ValidationOutput(BaseModel):
    ok: bool
    risk_level: Literal["low", "medium", "high"]
    findings: List[RuleFinding] = Field(default_factory=lambda: [])
    normalized_sql: str | None = None
