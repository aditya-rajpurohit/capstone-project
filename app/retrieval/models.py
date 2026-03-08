import uuid
from datetime import datetime, timezone
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.data_source.base import Base


class EmbeddingRecord(Base):
    __tablename__ = "embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # "schema" | "trace_examples"
    index: Mapped[str] = mapped_column(String(64), nullable=False)

    # stable external id for dedupe/upsert (e.g. "schema:<data_source_id>:<table>")
    doc_id: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)

    text: Mapped[str] = mapped_column(Text, nullable=False)
    meta_data: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    # embedding vector
    embedding: Mapped[list[float]] = mapped_column(
        Vector(1536), nullable=False
    )  # adjust dim to your embedder

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


Index("ix_embeddings_index", EmbeddingRecord.index)
