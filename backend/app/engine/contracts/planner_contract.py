from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class PlannerEntity(BaseModel):
    name: str = Field(..., min_length=1)
    type: Optional[str] = None


class PlannerConstraint(BaseModel):
    kind: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)


class PlannerOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: str
    operation: Literal["SELECT"] = "SELECT"
    entities: list[PlannerEntity] = Field(default_factory=list)
    constraints: list[PlannerConstraint] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
