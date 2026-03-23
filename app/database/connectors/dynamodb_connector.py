import json
from typing import Any

import aioboto3

from app.core.constants import DatabaseDialect
from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.base_connector import BaseConnector


class DynamoDBConnector(BaseConnector):

    def __init__(self, region: str) -> None:
        self._region = region
        self._session = None
        self._client = None
        self.dialect = DatabaseDialect.DYNAMODB

    async def connect(self) -> None:
        if self._client is None:
            self._session = aioboto3.Session()
            self._client = await self._session.client(
                "dynamodb", region_name=self._region
            ).__aenter__()

    async def close(self) -> None:
        if self._client:
            await self._client.__aexit__(None, None, None)

        self._client = None
        self._session = None

    async def health_check(self) -> bool:
        if self._client is None:
            return False

        try:
            await self._client.list_tables(Limit=1)
            return True
        except Exception:
            return False

    async def execute(self, sql: str) -> list[dict[str, Any]]:
        """
        Accept JSON query for DynamoDB.
        """
        if self._client is None:
            raise DataSourceExecutionError("ERROR: DynamoDBConnector not connected")

        try:
            query = json.loads(sql)

            table = query["table"]
            key = query.get("key")

            result = await self._client.get_item(
                TableName=table,
                Key=key,
            )

            item = result.get("Item")

            return [item] if item else []

        except Exception as e:
            raise DataSourceExecutionError(str(e)) from e

    async def introspect_schema(self) -> dict[str, Any]:
        if self._client is None:
            raise DataSourceExecutionError("ERROR: DynamoDBConnector not connected")

        snapshot = {"tables": []}

        tables = await self._client.list_tables()

        for table in tables.get("TableNames", []):
            snapshot["tables"].append(
                {
                    "name": table,
                    "columns": [],
                    "foreign_keys": [],
                }
            )

        return snapshot
