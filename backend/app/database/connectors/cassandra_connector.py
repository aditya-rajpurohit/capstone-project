from typing import Any

from cassandra.cluster import Cluster

from app.core.constants import DatabaseDialect
from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.base_connector import BaseConnector


class CassandraConnector(BaseConnector):

    def __init__(self, hosts: list[str], keyspace: str) -> None:
        self._hosts = hosts
        self._keyspace = keyspace
        self._cluster = None
        self._session = None
        self.dialect = DatabaseDialect.CASSANDRA

    async def connect(self) -> None:
        if self._session is None:
            self._cluster = Cluster(self._hosts)
            self._session = self._cluster.connect(self._keyspace)

    async def close(self) -> None:
        if self._cluster:
            self._cluster.shutdown()

        self._cluster = None
        self._session = None

    async def health_check(self) -> bool:
        if self._session is None:
            return False

        try:
            self._session.execute("SELECT now() FROM system.local")
            return True
        except Exception:
            return False

    async def execute(self, sql: str) -> list[dict[str, Any]]:
        if self._session is None:
            raise DataSourceExecutionError("ERROR: CassandraConnector not connected")

        try:
            rows = self._session.execute(sql)
            return [dict(r._asdict()) for r in rows]
        except Exception as e:
            raise DataSourceExecutionError(str(e)) from e

    async def introspect_schema(self) -> dict[str, Any]:
        if self._session is None:
            raise DataSourceExecutionError("ERROR: CassandraConnector not connected")

        snapshot = {"tables": []}

        tables = self._session.execute("SELECT table_name FROM system_schema.tables")

        for t in tables:
            snapshot["tables"].append(
                {
                    "name": t.table_name,
                    "columns": [],
                    "foreign_keys": [],
                }
            )

        return snapshot
