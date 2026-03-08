from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DatabaseDialect
from app.data_source.models.data_source import DataSourceConfigModel
from app.tools.db_connector.base_connector import BaseConnector
from app.tools.db_connector.postgres_connector import PostgresConnector


@dataclass
class DataSourceHandle:
    id: str
    name: str
    dialect: DatabaseDialect
    connector: BaseConnector
    is_active: bool = True
    is_healthy: bool = True


class DatabaseRegistry:

    _instance = None

    def __init__(self) -> None:
        self._db_units: dict[str, DataSourceHandle] = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # -----------------------------
    # Public API
    # -----------------------------

    def get(self, db_id: str) -> Optional[DataSourceHandle]:
        return self._db_units.get(db_id)

    def list_all(self) -> list[DataSourceHandle]:
        return list(self._db_units.values())

    def list_healthy(self) -> list[DataSourceHandle]:
        return [db for db in self._db_units.values() if db.is_active and db.is_healthy]

    def mark_unhealthy(self, db_id: str) -> None:
        if db_id in self._db_units:
            self._db_units[db_id].is_healthy = False

    # -----------------------------
    # App DB Loader
    # -----------------------------

    async def load_from_appdb(self, session: AsyncSession) -> None:
        statement = select(DataSourceConfigModel).where(
            DataSourceConfigModel.is_active == True
        )  # noqa: E712
        result = await session.execute(statement)
        rows = result.scalars().all()

        self._db_units = {}

        for row in rows:
            connector = self._build_connector(row)
            await connector.connect()

            self._db_units[str(row.id)] = DataSourceHandle(
                id=str(row.id),
                name=row.name,
                dialect=row.dialect,
                connector=connector,
                is_active=row.is_active,
                is_healthy=True,
            )

    # -----------------------------
    # Connector Factory
    # -----------------------------

    def _build_connector(self, row: DataSourceConfigModel) -> BaseConnector:

        # NOTE: replace this with proper decrypt from app/core/security
        password = row.encrypted_password or ""

        if row.dialect == DatabaseDialect.POSTGRES:
            dsn = (
                f"postgresql://{row.username}:{password}"
                f"@{row.host}:{row.port}/{row.database_name}"
            )
            return PostgresConnector(dsn)

        # if row.dialect == DatabaseDialect.MYSQL:
        #     dsn = (
        #         f"mysql://{row.username}:{password}"
        #         f"@{row.host}:{row.port}/{row.database_name}"
        #     )
        #     return MySQLConnector(dsn)

        # if row.dialect == DatabaseDialect.MONGO:
        #     dsn = (row.extra_config or {}).get("dsn")
        #     return MongoDBConnector(dsn)

        raise ValueError(f"Unsupported db_type: {row.dialect}")
