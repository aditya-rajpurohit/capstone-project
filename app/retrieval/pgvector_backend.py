from sqlalchemy import select

from app.data_source.session import get_sessionmaker
from app.retrieval.backend import RetrievalBackend
from app.retrieval.embedder import Embedder
from app.retrieval.models import EmbeddingRecord
from app.retrieval.types import RetrievalDocument, RetrievalHit, RetrievalQuery


class PgvectorBackend(RetrievalBackend):
    """
    Backend-agnostic interface, pgvector implementation.

    - Upsert by doc_id
    - Search by cosine distance (pgvector operator)
    """

    def __init__(self, embedder: Embedder, embedding_dim: int = 1536) -> None:
        self.embedder = embedder
        self.embedding_dim = embedding_dim

    async def upsert(self, retrieval_documents: list[RetrievalDocument]) -> None:
        if not retrieval_documents:
            return

        embeddings = await self.embedder.embed([d.text for d in retrieval_documents])

        Session = get_sessionmaker()

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

    async def search(self, retrieval_queries: RetrievalQuery) -> list[RetrievalHit]:
        q_emb = (await self.embedder.embed([retrieval_queries.query_text]))[0]

        Session = get_sessionmaker()

        async with Session() as session:
            stmt = select(EmbeddingRecord).where(
                EmbeddingRecord.index == retrieval_queries.index
            )

            # Optional metadata filter (MVP: exact match on keys)
            if retrieval_queries.metadata_filter:
                for k, v in retrieval_queries.metadata_filter.items():
                    stmt = stmt.where(EmbeddingRecord.meta_data[k].astext == str(v))

            # Order by cosine distance (pgvector)
            stmt = stmt.order_by(
                EmbeddingRecord.embedding.cosine_distance(q_emb)
            ).limit(retrieval_queries.top_k)

            rows = (await session.scalars(stmt)).all()

            # Convert distance -> score (simple: score = 1 - distance, clamp later if needed)
            hits: list[RetrievalHit] = []
            for r in rows:
                # we don't have the actual distance without selecting it; keep score as placeholder
                hits.append(
                    RetrievalHit(
                        id=r.doc_id,
                        index=retrieval_queries.index,
                        score=0.0,
                        text=r.text,
                        metadata=r.meta_data,
                    )
                )

            return hits
