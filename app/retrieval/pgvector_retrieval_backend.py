from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from app.retrieval.retrieval_backend import RetrievalBackend
from app.retrieval.embedding_interface import Embedder
from app.retrieval.retrieval_types import RetrievalDocument, RetrievalHit, RetrievalIndex, RetrievalQuery
from app.retrieval.embedding_models import EmbeddingRecord
from app.database.metadata.session import get_async_session


class PgvectorBackend(RetrievalBackend):
    """
    Backend-agnostic interface, pgvector implementation.

    - Upsert by doc_id
    - Search by cosine distance (pgvector operator)
    """
    def __init__(
        self,
        embedder: Embedder,
        embedding_dim: int = 1536,
        sessionmaker: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self.embedder = embedder
        self.embedding_dim = embedding_dim
        self._Session = sessionmaker or get_async_session()


    async def upsert(self, retrieval_documents: list[RetrievalDocument]) -> None:
        if not retrieval_documents:
            return

        embeddings = await self.embedder.embed([doc.text for doc in retrieval_documents])

        Session = get_async_session()

        async with Session() as session:
            for doc, emb in zip(retrieval_documents, embeddings, strict=True):
                # Upsert by doc_id (unique)
                existing = await session.scalar(
                    select(EmbeddingRecord).where(EmbeddingRecord.doc_id == doc.id)
                )
                if existing:
                    existing.index = doc.index
                    existing.text = doc.text
                    existing.meta_data = doc.metadata
                    existing.embedding = emb
                else:
                    session.add(
                        EmbeddingRecord(
                            doc_id=doc.id,
                            index=doc.index,
                            text=doc.text,
                            metadata=doc.metadata,
                            embedding=emb,
                        )
                    )
            await session.commit()


    async def search(self, retrieval_query: RetrievalQuery) -> list[RetrievalHit]:
        q_embedding = (await self.embedder.embed([retrieval_query.query_text]))[0]

        if len(q_embedding) != self.embedding_dim:
            raise ValueError("Query embedding dimension mismatch")

        async with self._Session() as session:
            stmt = select(EmbeddingRecord).where(
                EmbeddingRecord.index == retrieval_query.index
            )

            if retrieval_query.metadata_filter:
                for k, v in retrieval_query.metadata_filter.items():
                    stmt = stmt.where(
                        EmbeddingRecord.meta_data[k].astext == str(v)
                    )

            stmt = stmt.order_by(
                EmbeddingRecord.embedding.cosine_distance(q_embedding)
            ).limit(retrieval_query.top_k)

            records = (await session.scalars(stmt)).all()

            hits: list[RetrievalHit] = []

            for record in records:
                hits.append(
                    RetrievalHit(
                        id=record.doc_id,
                        index=retrieval_query.index,
                        score=0.0,
                        text=record.text,
                        metadata=record.meta_data,
                    )
                )

            return hits
