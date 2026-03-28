from typing import Optional

from pydantic import BaseModel, Field


class QueryOutput(BaseModel):
    sql: str = Field(..., min_length=1)
    explanation: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
