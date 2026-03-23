from typing import Any

import aiosqlite

from app.core.constants import DatabaseDialect
from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.base_connector import BaseConnector


class SQLiteConnector(BaseConnector):

    def __init__(self, path: str) -> None:
        self._path = path
        self._conn: aiosqlite.Connection | None = None
        self.dialect = DatabaseDialect.SQLITE

    async def connect(self) -> None:
        if self._conn is None:
            self._conn = await aiosqlite.connect(self._path)
            self._conn.row_factory = aiosqlite.Row

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
        self._conn = None

    async def health_check(self) -> bool:
        if self._conn is None:
            return False

        try:
            async with self._conn.execute("SELECT 1"):
                return True
        except Exception:
            return False

    async def execute(self, sql: str) -> list[dict[str, Any]]:
        if self._conn is None:
            raise DataSourceExecutionError("ERROR: SQLiteConnector not connected")

        try:
            async with self._conn.execute(sql) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

        except Exception as e:
            raise DataSourceExecutionError(str(e)) from e

    async def introspect_schema(self) -> dict[str, Any]:
        if self._conn is None:
            raise DataSourceExecutionError("ERROR: SQLiteConnector not connected!")

        snapshot = {"tables": []}

        async with self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ) as cursor:

            tables = await cursor.fetchall()

        for table in tables:
            name = table["name"]

            columns_cursor = await self._conn.execute(f"PRAGMA table_info({name})")
            columns = await columns_cursor.fetchall()

            fk_cursor = await self._conn.execute(f"PRAGMA foreign_key_list({name})")
            foreign_keys = await fk_cursor.fetchall()

            snapshot["tables"].append(
                {
                    "name": name,
                    "columns": [
                        {
                            "name": c["name"],
                            "data_type": c["type"],
                            "is_nullable": not c["notnull"],
                        }
                        for c in columns
                    ],
                    "foreign_keys": [
                        {
                            "column": fk["from"],
                            "ref_table": fk["table"],
                            "ref_column": fk["to"],
                        }
                        for fk in foreign_keys
                    ],
                }
            )

        return snapshot
