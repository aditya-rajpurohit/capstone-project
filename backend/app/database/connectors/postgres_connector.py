from typing import Any

import asyncpg

from app.core.constants import DatabaseDialect
from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.base_connector import BaseConnector


class PostgresConnector(BaseConnector):

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None
        self.dialect = DatabaseDialect.POSTGRES

    async def connect(self) -> None:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(dsn=self._dsn)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
        self._pool = None

    async def health_check(self) -> bool:
        if not self._pool:
            return False

        try:
            async with self._pool.acquire() as connection:
                await connection.execute("SELECT 1")
            return True
        except Exception:
            return False

    async def execute(self, sql: str) -> list[dict[str, Any]]:
        if self._pool is None:
            raise DataSourceExecutionError("ERROR: PostgresConnector not connected!")

        try:
            async with self._pool.acquire() as connection:
                rows = await connection.fetch(sql)
                return [dict(r) for r in rows]

        except Exception as e:
            raise DataSourceExecutionError(str(e)) from e

    async def introspect_schema(self) -> dict[str, Any]:
        if self._pool is None:
            raise DataSourceExecutionError("ERROR: PostgresConnector not connected!")

        snapshot = {"tables": []}

        async with self._pool.acquire() as connection:

            tables = await connection.fetch("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema='public'
                AND table_type='BASE TABLE'
            """)

            for table in tables:

                name = table["table_name"]

                columns = await connection.fetch(
                    """
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = $1
                    """,
                    name,
                )

                foreign_keys = await connection.fetch(
                    """
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS ref_table,
                        ccu.column_name AS ref_column
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type='FOREIGN KEY'
                    AND tc.table_name = $1
                    """,
                    name,
                )

                snapshot["tables"].append(
                    {
                        "name": name,
                        "columns": [
                            {
                                "name": c["column_name"],
                                "data_type": c["data_type"],
                                "is_nullable": c["is_nullable"] == "YES",
                            }
                            for c in columns
                        ],
                        "foreign_keys": [
                            {
                                "column": fk["column_name"],
                                "ref_table": fk["ref_table"],
                                "ref_column": fk["ref_column"],
                            }
                            for fk in foreign_keys
                        ],
                    }
                )

        return snapshot
