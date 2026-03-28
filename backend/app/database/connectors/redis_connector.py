from typing import Any

import redis.asyncio as redis

from app.core.constants import DatabaseDialect
from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.base_connector import BaseConnector


class RedisConnector(BaseConnector):

    def __init__(self, url: str) -> None:
        self._url = url
        self._client = None
        self.dialect = DatabaseDialect.REDIS

    async def connect(self) -> None:
        if self._client is None:
            self._client = redis.from_url(self._url)

    async def close(self) -> None:
        if self._client:
            await self._client.close()

        self._client = None

    async def health_check(self) -> bool:
        if self._client is None:
            return False

        try:
            self._client.ping()
            return True
        except Exception:
            return False

    async def execute(self, sql: str) -> list[dict[str, Any]]:
        if self._client is None:
            raise DataSourceExecutionError("ERROR: RedisConnector not connected")

        try:
            parts = sql.split()

            cmd = parts[0].lower()

            if cmd == "get":
                val = await self._client.get(parts[1])
                return [{"value": val}]

            if cmd == "keys":
                keys = await self._client.keys("*")
                return [{"key": k} for k in keys]

            return []

        except Exception as e:
            raise DataSourceExecutionError(str(e)) from e

    async def introspect_schema(self) -> dict[str, Any]:
        if self._client is None:
            raise DataSourceExecutionError("ERROR: RedisConnector not connected")

        snapshot = {"tables": []}

        keys = await self._client.keys("*")

        snapshot["tables"].append(
            {
                "name": "keys",
                "columns": [{"name": "key", "data_type": "string"}],
                "foreign_keys": [],
            }
        )

        return snapshot
