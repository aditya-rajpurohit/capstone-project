from typing import Literal

from pydantic import BaseModel, Field


class PlannerEntity(BaseModel):
    name: str = Field(..., min_length=1)
    type: str | None = None


class PlannerConstraint(BaseModel):
    kind: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)


class PlannerOutput(BaseModel):
    intent: str = Field(..., min_length=1)
    operation: Literal["SELECT"] = "SELECT"
    entities: list[PlannerEntity] = Field(default_factory=lambda: [])
    constraints: list[PlannerConstraint] = Field(default_factory=lambda: [])
    confidence: float = Field(..., ge=0.0, le=1.0)
