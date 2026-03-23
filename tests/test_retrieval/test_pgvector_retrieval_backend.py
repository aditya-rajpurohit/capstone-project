from unittest.mock import AsyncMock

import pytest

from app.retrieval.pgvector_retrieval_backend import PgvectorBackend
from app.retrieval.retrieval_types import RetrievalQuery


@pytest.mark.asyncio
async def test_upsert_empty_documents():
    embedder = AsyncMock()
    backend = PgvectorBackend(embedder)

    await backend.upsert([])

    embedder.embed.assert_not_called()


@pytest.mark.asyncio
async def test_search_embedding_dimension_mismatch():
    embedder = AsyncMock()
    embedder.embed.return_value = [[1, 2, 3]]  # wrong dimension

    backend = PgvectorBackend(embedder, embedding_dim=1536)

    query = RetrievalQuery(index="schema", query_text="test")

    with pytest.raises(ValueError):
        await backend.search(query)
