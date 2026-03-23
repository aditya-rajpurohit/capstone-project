from typing import Any

import duckdb

from app.core.constants import DatabaseDialect
from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.base_connector import BaseConnector


class DuckDBConnector(BaseConnector):

    def __init__(self, path: str) -> None:
        self._path = path
        self._conn = None
        self.dialect = DatabaseDialect.DUCKDB

    async def connect(self) -> None:
        if self._conn is None:
            self._conn = duckdb.connect(self._path)

    async def close(self) -> None:
        if self._conn:
            self._conn.close()

        self._conn = None

    async def health_check(self) -> bool:
        if self._conn is None:
            return False

        try:
            await self.execute("SELECT 1")
            return True
        except Exception:
            return False

    async def execute(self, sql: str) -> list[dict[str, Any]]:
        if self._conn is None:
            raise DataSourceExecutionError("ERROR: DuckDBConnector not connected")

        try:
            cur = self._conn.execute(sql)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            return [dict(zip(cols, r)) for r in rows]

        except Exception as e:
            raise DataSourceExecutionError(str(e)) from e

    async def introspect_schema(self) -> dict[str, Any]:

        snapshot = {"tables": []}

        tables = await self.execute("SHOW TABLES")

        for table in tables:

            name = list(table.values())[0]

            columns = await self.execute(f"PRAGMA table_info('{name}')")

            snapshot["tables"].append(
                {
                    "name": name,
                    "columns": columns,
                    "foreign_keys": [],
                }
            )

        return snapshot
