from dataclasses import dataclass
from typing import Any, Literal, Optional

RetrievalIndex = Literal["schema", "trace_examples"]


@dataclass(frozen=True)
class RetrievalDocument:
    id: str
    index: RetrievalIndex
    text: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class RetrievalHit:
    id: str
    index: RetrievalIndex
    score: float
    text: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class RetrievalQuery:
    index: RetrievalIndex
    query_text: str
    top_k: int = 5
    metadata_filter: Optional[dict[str, Any]] = None
