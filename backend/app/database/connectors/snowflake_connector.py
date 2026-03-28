import asyncio
from typing import Any

import snowflake.connector
from snowflake.connector import SnowflakeConnection

from app.core.constants import DatabaseDialect
from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.base_connector import BaseConnector


class SnowflakeConnector(BaseConnector):

    def __init__(
        self, user: str, password: str, account: str, database: str, warehouse: str
    ) -> None:
        self._user = user
        self._password = password
        self._account = account
        self._database = database
        self._warehouse = warehouse
        self._conn: SnowflakeConnection | None = None
        self.dialect = DatabaseDialect.SNOWFLAKE

    async def connect(self) -> None:
        if self._conn is None:
            loop = asyncio.get_running_loop()
            self._conn = await loop.run_in_executor(
                None,
                lambda: snowflake.connector.connect(
                    user=self._user,
                    password=self._password,
                    account=self._account,
                    warehouse=self._warehouse,
                    database=self._database,
                ),
            )

    async def close(self) -> None:
        if self._conn:
            await asyncio.get_running_loop().run_in_executor(None, self._conn.close)

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
            raise DataSourceExecutionError("ERROR: SnowflakeConnector not connected")

        conn: SnowflakeConnection = self._conn

        try:
            loop = asyncio.get_running_loop()

            def _run():
                cur = conn.cursor()
                cur.execute(sql)
                cols = [c[0] for c in cur.description]
                rows = cur.fetchall()
                return [dict(zip(cols, r)) for r in rows]

            return await loop.run_in_executor(None, _run)

        except Exception as e:
            raise DataSourceExecutionError(str(e)) from e

    async def introspect_schema(self) -> dict[str, Any]:
        snapshot: dict[str, Any] = {"tables": []}

        tables = await self.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema='PUBLIC'
        """)

        for table in tables:

            name = table["TABLE_NAME"]

            columns = await self.execute(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name='{name}'
            """)

            snapshot["tables"].append(
                {
                    "name": name,
                    "columns": columns,
                    "foreign_keys": [],
                }
            )

        return snapshot
