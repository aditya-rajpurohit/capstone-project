import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database.metadata.models.base import Base


class ChatSessionModel(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    session_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)

    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    turns: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=lambda: [])

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
