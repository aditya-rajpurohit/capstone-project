from typing import List, Literal

from pydantic import BaseModel, Field


class RuleFinding(BaseModel):
    rule_id: str
    severity: Literal["low", "medium", "high"]
    message: str


class ValidationOutput(BaseModel):
    ok: bool
    risk_level: Literal["low", "medium", "high"]
    limit_injected: bool = False
    limit_value: int | None = None
    contains_select_star: bool = False
    normalized_sql: str | None = None
    # findings: List[RuleFinding] = Field(default_factory=lambda: [])
    # confidence_score: float
