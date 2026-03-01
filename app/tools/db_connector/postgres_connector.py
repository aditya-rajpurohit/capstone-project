from typing import Any

import asyncpg

from app.core.constants import DatabaseDialect
from app.tools.db_connector.base_connector import BaseConnector


class PostgresConnector(BaseConnector):

    def __init__(self, dsn: str) -> None:
        """TODO"""
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None
        self.dialect = DatabaseDialect.POSTGRES

    async def connect(self) -> None:
        if not self._pool:
            self._pool = await asyncpg.create_pool(dsn=self._dsn)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

        self._pool = None

    async def execute(self, sql: str) -> list[dict[str, Any]]:
        if not self._pool:
            raise RuntimeError("Error: PostgresConnector not connected!")

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(sql)
            return [dict(row) for row in rows]

    async def introspect_schema(self) -> list[dict[str, Any]]:
        if not self._pool:
            raise RuntimeError("Error: PostgresConnector not connected!")

        async with self._pool.acquire() as connection:
            tables = await connection.fetch("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
            """)

            schema_snapshot: list[dict[str, Any]] = []

            for table in tables:
                table_name = table["table_name"]

                columns = await connection.fetch(
                    """
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = $1
                """,
                    table_name,
                )

                foreign_keys = await connection.fetch(
                    """
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_name = $1
                """,
                    table_name,
                )

                schema_snapshot.append(
                    {
                        "table_name": table_name,
                        "columns": [dict(c) for c in columns],
                        "foreign_keys": [dict(fk) for fk in foreign_keys],
                    }
                )

            return schema_snapshot
