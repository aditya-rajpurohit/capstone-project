import asyncio
from typing import Any

from google.cloud import bigquery

from app.core.constants import DatabaseDialect
from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.base_connector import BaseConnector


class BigQueryConnector(BaseConnector):

    def __init__(self, project: str, dataset: str) -> None:
        self._project = project
        self._dataset = dataset
        self._client = None
        self.dialect = DatabaseDialect.BIGQUERY

    async def connect(self) -> None:
        if self._client is None:
            self._client = bigquery.Client(project=self._project)

    async def close(self) -> None:
        self._client = None

    async def health_check(self) -> bool:
        if self._client is None:
            return False

        try:
            await self.execute("SELECT 1")
            return True
        except Exception:
            return False

    async def execute(self, sql: str):
        if self._client is None:
            raise DataSourceExecutionError("ERROR: BigQueryConnector not connected")

        client = self._client

        try:
            loop = asyncio.get_running_loop()

            def _run():
                job = client.query(sql)
                rows = job.result()
                return [dict(r.items()) for r in rows]

            return await loop.run_in_executor(None, _run)

        except Exception as e:
            raise DataSourceExecutionError(str(e)) from e

    async def introspect_schema(self):
        snapshot: dict[str, Any] = {"tables": []}

        tables = await self.execute(f"""
            SELECT table_name
            FROM `{self._project}.{self._dataset}.INFORMATION_SCHEMA.TABLES`
        """)

        for table in tables:

            name = table["table_name"]

            columns = await self.execute(f"""
                SELECT column_name, data_type
                FROM `{self._project}.{self._dataset}.INFORMATION_SCHEMA.COLUMNS`
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
