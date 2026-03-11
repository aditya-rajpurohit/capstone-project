from typing import Literal, Optional
from pydantic import BaseModel, Field


class ValidationOutput(BaseModel):
    ok: bool
    risk_level: Literal["low", "medium", "high"]
    limit_injected: bool = Field(default=False)
    limit_value: Optional[int] = Field(default=None, ge=0)
    contains_select_star: bool = Field(default=False)
    normalized_sql: Optional[str] = None
