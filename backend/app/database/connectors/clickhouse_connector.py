from typing import Any

import clickhouse_connect

from app.core.constants import DatabaseDialect
from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.base_connector import BaseConnector


class ClickHouseConnector(BaseConnector):

    def __init__(self, host: str, database: str) -> None:
        self._host = host
        self._database = database
        self._client = None
        self.dialect = DatabaseDialect.CLICKHOUSE

    async def connect(self) -> None:
        if self._client is None:
            self._client = clickhouse_connect.get_client(
                host=self._host,
                database=self._database,
            )

    async def close(self):
        self._client = None

    async def health_check(self) -> bool:
        if self._client is None:
            return False

        try:
            await self.execute("SELECT 1")
            return True
        except Exception:
            return False

    async def execute(self, sql: str) -> list[dict[str, Any]]:
        if self._client is None:
            raise DataSourceExecutionError("ERROR: ClickHouseConnector not connected")

        try:
            result = self._client.query(sql)
            cols = result.column_names
            rows = [dict(zip(cols, row)) for row in result.result_rows]
            return rows

        except Exception as e:
            raise DataSourceExecutionError(str(e)) from e

    async def introspect_schema(self) -> dict[str, Any]:
        snapshot = {"tables": []}

        tables = await self.execute("SHOW TABLES")

        for table in tables:

            name = list(table.values())[0]

            columns = await self.execute(f"DESCRIBE TABLE {name}")

            snapshot["tables"].append(
                {
                    "name": name,
                    "columns": columns,
                    "foreign_keys": [],
                }
            )

        return snapshot
