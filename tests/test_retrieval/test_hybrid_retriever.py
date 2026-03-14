import pytest
from unittest.mock import AsyncMock

from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.retrieval_types import RetrievalHit


@pytest.mark.asyncio
async def test_retrieve_schema_hits():
    backend = AsyncMock()
    backend.search.return_value = [
        RetrievalHit(id="1", index="schema", score=1.0, text="users", metadata={})
    ]

    retriever = HybridRetriever(backend)

    hits = await retriever.retrieve_schema_hits("users")

    backend.search.assert_awaited_once()
    assert len(hits) == 1
    assert hits[0].id == "1"


@pytest.mark.asyncio
async def test_retrieve_trace_hits():
    backend = AsyncMock()
    backend.search.return_value = []

    retriever = HybridRetriever(backend)

    hits = await retriever.retrieve_trace_hits("query")

    backend.search.assert_awaited_once()
    assert hits == []
