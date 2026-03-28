from typing import Any, LiteralString, cast

from neo4j import AsyncGraphDatabase, Query

from app.core.constants import DatabaseDialect
from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.base_connector import BaseConnector


class Neo4jConnector(BaseConnector):

    def __init__(self, uri: str, user: str, password: str) -> None:
        self._uri = uri
        self._user = user
        self._password = password
        self._driver = None
        self.dialect = DatabaseDialect.NEO4J

    async def connect(self) -> None:
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                self._uri, auth=(self._user, self._password)
            )

    async def close(self) -> None:
        if self._driver:
            await self._driver.close()

        self._driver = None

    async def health_check(self) -> bool:
        if self._driver is None:
            return False

        try:
            async with self._driver.session() as session:
                await session.run("RETURN 1")
            return True
        except Exception:
            return False

    async def execute(self, sql: str) -> list[dict[str, Any]]:
        """
        Cypher query
        """
        if self._driver is None:
            raise DataSourceExecutionError("ERROR: Neo4jConnector not connected")

        try:
            async with self._driver.session() as session:

                result = await session.run(Query(cast(LiteralString, sql)))

                rows = []
                async for record in result:
                    rows.append(dict(record))

                return rows

        except Exception as e:
            raise DataSourceExecutionError(str(e)) from e

    async def introspect_schema(self) -> dict[str, Any]:
        if self._driver is None:
            raise DataSourceExecutionError("ERROR: Neo4jConnector not connected")

        snapshot = {"tables": []}

        async with self._driver.session() as session:

            result = await session.run("CALL db.labels()")

            async for record in result:

                snapshot["tables"].append(
                    {
                        "name": record["label"],
                        "columns": [],
                        "foreign_keys": [],
                    }
                )

        return snapshot
