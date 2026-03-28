from typing import Any, Optional

from app.retrieval.retrieval_backend import RetrievalBackend
from app.retrieval.retrieval_types import RetrievalHit, RetrievalQuery


class HybridRetriever:
    """
    MVP: 2 retrieval calls:
      - schema hits (always)
      - trace_examples hits (always or gated)
    """

    def __init__(self, backend: RetrievalBackend) -> None:
        self.backend = backend

    async def retrieve_schema_hits(
        self,
        user_query: str,
        *,
        top_k: int = 8,
        metadata_filter: Optional[dict[str, Any]] = None
    ) -> list[RetrievalHit]:
        return await self.backend.search(
            RetrievalQuery(
                index="schema",
                query_text=user_query,
                top_k=top_k,
                metadata_filter=metadata_filter,
            )
        )

    async def retrieve_trace_hits(
        self,
        user_query: str,
        *,
        top_k: int = 5,
        metadata_filter: Optional[dict[str, Any]] = None
    ) -> list[RetrievalHit]:
        return await self.backend.search(
            RetrievalQuery(
                index="trace_examples",
                query_text=user_query,
                top_k=top_k,
                metadata_filter=metadata_filter,
            )
        )
