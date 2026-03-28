from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.neo4j_connector import Neo4jConnector


@pytest.mark.asyncio
async def test_connect():
    with patch(
        "app.database.connectors.neo4j_connector.AsyncGraphDatabase.driver"
    ) as mock_driver:

        connector = Neo4jConnector("bolt://localhost", "neo4j", "pass")

        driver = MagicMock()
        mock_driver.return_value = driver

        await connector.connect()

        assert connector._driver == driver


@pytest.mark.asyncio
async def test_close():
    connector = Neo4jConnector("uri", "user", "pass")

    driver = AsyncMock()
    connector._driver = driver

    await connector.close()

    driver.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_health_check_success():
    connector = Neo4jConnector("uri", "user", "pass")

    session = AsyncMock()

    session_ctx = AsyncMock()
    session_ctx.__aenter__.return_value = session

    driver = MagicMock()
    driver.session.return_value = session_ctx

    connector._driver = driver

    result = await connector.health_check()

    assert result is True


@pytest.mark.asyncio
async def test_execute():
    connector = Neo4jConnector("uri", "user", "pass")

    record = {"name": "Alice"}

    result_cursor = AsyncMock()
    result_cursor.__aiter__.return_value = [record]

    session = AsyncMock()
    session.run = AsyncMock(return_value=result_cursor)

    session_ctx = AsyncMock()
    session_ctx.__aenter__.return_value = session

    driver = MagicMock()
    driver.session.return_value = session_ctx

    connector._driver = driver

    result = await connector.execute("MATCH (n) RETURN n")

    assert result == [record]


@pytest.mark.asyncio
async def test_execute_not_connected():
    connector = Neo4jConnector("uri", "user", "pass")

    with pytest.raises(DataSourceExecutionError):
        await connector.execute("MATCH (n) RETURN n")


@pytest.mark.asyncio
async def test_introspect_schema():
    connector = Neo4jConnector("uri", "user", "pass")

    labels = [{"label": "User"}]

    cursor = AsyncMock()
    cursor.__aiter__.return_value = labels

    session = AsyncMock()
    session.run = AsyncMock(return_value=cursor)

    session_ctx = AsyncMock()
    session_ctx.__aenter__.return_value = session

    driver = MagicMock()
    driver.session.return_value = session_ctx

    connector._driver = driver

    result = await connector.introspect_schema()

    assert result["tables"][0]["name"] == "User"
