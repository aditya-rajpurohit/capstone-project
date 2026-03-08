import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import DatabaseDialect
from app.data_source.base import Base


class DataSourceConfigModel(Base):
    """
    Persistent configuration for a registered data source.
    Represents one DB server + credentials.
    """

    __tablename__ = "data_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    dialect: Mapped[DatabaseDialect] = mapped_column(
        String(50),
        nullable=False,
    )  # POSTGRES/MYSQL/MONGODB
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    host: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    database_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    encrypted_password: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    extra_config: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False
    )
