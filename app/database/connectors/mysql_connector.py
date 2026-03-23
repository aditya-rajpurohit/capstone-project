from typing import Any
from urllib.parse import urlparse

import aiomysql

from app.core.constants import DatabaseDialect
from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.base_connector import BaseConnector


class MySQLConnector(BaseConnector):

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: aiomysql.Pool | None = None
        self.dialect = DatabaseDialect.MYSQL

    async def connect(self) -> None:
        if self._pool is not None:
            return

        parsed = urlparse(self._dsn)

        self._pool = await aiomysql.create_pool(
            host=parsed.hostname,
            port=parsed.port or 3306,
            user=parsed.username,
            password=parsed.password,
            db=parsed.path.lstrip("/"),
        )

    async def close(self) -> None:
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()

        self._pool = None

    async def health_check(self) -> bool:
        if self._pool is None:
            return False

        try:
            async with self._pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute("SELECT 1")
            return True
        except Exception:
            return False

    async def execute(self, sql: str) -> list[dict[str, Any]]:
        if self._pool is None:
            raise DataSourceExecutionError("ERROR: MySQLConnector not connected!")

        try:
            async with self._pool.acquire() as connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql)
                    rows = await cursor.fetchall()
                    return list(rows)

        except Exception as e:
            raise DataSourceExecutionError(str(e)) from e

    async def introspect_schema(self) -> dict[str, Any]:
        if self._pool is None:
            raise DataSourceExecutionError("ERROR: MySQLConnector not connected!")

        snapshot = {"tables": []}

        async with self._pool.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:

                await cursor.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema=DATABASE()
                """)

                tables = await cursor.fetchall()

                for table in tables:

                    name = table["table_name"]

                    await cursor.execute(
                        """
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_name=%s
                        AND table_schema=DATABASE()
                        """,
                        (name),
                    )
                    columns = await cursor.fetchall()

                    await cursor.execute(
                        """
                        SELECT
                            column_name,
                            referenced_table_name AS ref_table,
                            referenced_column_name AS ref_column
                        FROM information_schema.key_column_usage
                        WHERE table_name = %s
                        AND referenced_table_name IS NOT NULL
                        AND table_schema = DATABASE()
                        """,
                        (name),
                    )
                    foreign_keys = await cursor.fetchall()

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
