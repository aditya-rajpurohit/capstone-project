import json
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.constants import DatabaseDialect
from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.base_connector import BaseConnector


class MongoDBConnector(BaseConnector):

    def __init__(self, uri: str, db_name: str) -> None:
        self._uri = uri
        self._db_name = db_name
        self._client: AsyncIOMotorClient | None = None
        self._db: AsyncIOMotorDatabase | None = None
        self.dialect = DatabaseDialect.MONGODB

    async def connect(self) -> None:
        if self._client is None:
            self._client = AsyncIOMotorClient(self._uri)
            self._db = self._client[self._db_name]

    async def close(self) -> None:
        if self._client:
            self._client.close()

        self._client = None
        self._db = None

    async def health_check(self) -> bool:
        if self._client is None:
            return False

        try:
            await self._client.admin.command("ping")
            return True
        except Exception:
            return False

    async def execute(self, sql: str) -> list[dict[str, Any]]:
        """
        Accept JSON string query:
        {
            "collection": "users",
            "filter": {}
        }
        """
        if self._db is None:
            raise DataSourceExecutionError("ERROR: MongoDBConnector not connected!")

        try:
            query = json.loads(sql)

            collection = self._db[query["collection"]]
            cursor = collection.find(query.get("filter", {}))

            return [doc async for doc in cursor]

        except Exception as e:
            raise DataSourceExecutionError(str(e)) from e

    async def introspect_schema(self) -> dict[str, Any]:
        if self._db is None:
            raise DataSourceExecutionError("ERROR: MongoDBConnector not connected!")

        snapshot = {"tables": []}

        collections = await self._db.list_collection_names()

        for name in collections:
            snapshot["tables"].append(
                {
                    "name": name,
                    "columns": [],
                    "foreign_keys": [],
                }
            )

        return snapshot
