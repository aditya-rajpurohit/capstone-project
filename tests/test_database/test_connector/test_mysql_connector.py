from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.mysql_connector import MySQLConnector


@pytest.mark.asyncio
async def test_connect_creates_pool():

    connector = MySQLConnector("fake_dsn")

    with patch(
        "app.database.connectors.mysql_connector.aiomysql.create_pool",
        new_callable=AsyncMock,
    ) as mock_pool:

        await connector.connect()

        assert connector._pool is not None
        mock_pool.assert_called_once()


@pytest.mark.asyncio
async def test_close_closes_pool():

    connector = MySQLConnector("fake_dsn")

    pool = AsyncMock()
    connector._pool = pool

    await connector.close()

    pool.close.assert_called_once()
    pool.wait_closed.assert_awaited_once()


@pytest.mark.asyncio
async def test_health_check_success():

    connector = MySQLConnector("fake_dsn")

    cursor = AsyncMock()
    cursor.execute = AsyncMock()

    conn = MagicMock()
    conn.cursor.return_value.__aenter__.return_value = cursor
    conn.cursor.return_value.__aexit__.return_value = None

    pool = MagicMock()
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.acquire.return_value.__aexit__.return_value = None

    connector._pool = pool

    result = await connector.health_check()

    assert result is True
    cursor.execute.assert_awaited_once_with("SELECT 1")


@pytest.mark.asyncio
async def test_execute_returns_rows():

    connector = MySQLConnector("fake_dsn")

    cursor = AsyncMock()
    cursor.fetchall = AsyncMock(return_value=[{"id": 1}])
    cursor.execute = AsyncMock()

    conn = MagicMock()
    conn.cursor.return_value.__aenter__.return_value = cursor
    conn.cursor.return_value.__aexit__.return_value = None

    pool = MagicMock()
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.acquire.return_value.__aexit__.return_value = None

    connector._pool = pool

    result = await connector.execute("SELECT 1")

    assert result == [{"id": 1}]
    cursor.execute.assert_awaited_once_with("SELECT 1")


@pytest.mark.asyncio
async def test_execute_not_connected():

    connector = MySQLConnector("fake_dsn")

    with pytest.raises(DataSourceExecutionError):
        await connector.execute("SELECT 1")


@pytest.mark.asyncio
async def test_introspect_schema():

    connector = MySQLConnector("fake_dsn")

    cursor = AsyncMock()

    cursor.fetchall.side_effect = [
        [{"table_name": "users"}],  # tables
        [{"column_name": "id", "data_type": "int", "is_nullable": "NO"}],  # columns
        [],  # foreign keys
    ]

    conn = MagicMock()
    conn.cursor.return_value.__aenter__.return_value = cursor
    conn.cursor.return_value.__aexit__.return_value = None

    pool = MagicMock()
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.acquire.return_value.__aexit__.return_value = None

    connector._pool = pool

    result = await connector.introspect_schema()

    assert result["tables"][0]["name"] == "users"
