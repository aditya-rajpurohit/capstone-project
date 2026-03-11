from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DatabaseDialect
from app.database.metadata.models.data_source import DataSourceConfigModel
from app.database.connector.base_connector import BaseConnector
from app.database.connector.postgres_connector import PostgresConnector


@dataclass
class DataSourceHandle:
    id: str
    name: str
    dialect: DatabaseDialect
    connector: BaseConnector
    is_active: bool = True
    is_healthy: bool = True
    freshness_ttl_seconds: int = 300


class DatabaseRegistry:

    _instance: Optional["DatabaseRegistry"] = None

    def __init__(self) -> None:
        self._handles: dict[str, DataSourceHandle] = {}

    @classmethod
    def get_instance(cls) -> "DatabaseRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # -----------------------------
    # Public API
    # -----------------------------

    def get(self, data_source_id: str) -> Optional[DataSourceHandle]:
        return self._handles.get(data_source_id)

    def list_all(self) -> list[DataSourceHandle]:
        return list(self._handles.values())

    def list_healthy(self) -> list[DataSourceHandle]:
        return [
            h for h in self._handles.values()
            if h.is_active and h.is_healthy
        ]

    def mark_unhealthy(self, data_source_id: str) -> None:
        h = self._handles.get(data_source_id)
        if h:
            h.is_healthy = False

    # -----------------------------
    # App DB Loader
    # -----------------------------

    async def load_from_appdb(self, session: AsyncSession) -> None:
        stmt = select(DataSourceConfigModel).where(DataSourceConfigModel.is_active.is_(True))
        result = await session.execute(stmt)
        rows = result.scalars().all()

        self._handles = {}

        for row in rows:
            dialect = self._parse_dialect(row.dialect)

            connector = self._build_connector(row, dialect)

            is_healthy = True
            try:
                await connector.connect()
                is_healthy = await connector.health_check()
            except Exception:
                is_healthy = False

            self._handles[str(row.id)] = DataSourceHandle(
                id=str(row.id),
                name=row.name,
                dialect=dialect,
                connector=connector,
                is_active=bool(row.is_active),
                is_healthy=is_healthy,
                freshness_ttl_seconds=int(row.freshness_ttl_seconds or 300),
            )

    def _parse_dialect(self, value) -> DatabaseDialect:
        """
        Handles DB column storing either enum or string.
        """
        if isinstance(value, DatabaseDialect):
            return value
        return DatabaseDialect(str(value).upper())

    # -----------------------------
    # Connector Factory
    # -----------------------------

    def _build_connector(self, row: DataSourceConfigModel, dialect: DatabaseDialect) -> BaseConnector:
        # TODO: replace this with proper decrypt from app/core/security
        password = row.encrypted_password or ""
        username = row.username or ""

        if dialect == DatabaseDialect.POSTGRES:
            dsn = f"postgresql://{username}:{password}@{row.host}:{row.port}/{row.database_name}"
            return PostgresConnector(dsn)

        raise ValueError(f"Unsupported dialect: {dialect}")
