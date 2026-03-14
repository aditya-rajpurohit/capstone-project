import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.database.connector.postgres_connector import PostgresConnector
from app.core.exceptions import DataSourceExecutionError


@pytest.mark.asyncio
async def test_connect_creates_pool():
    connector = PostgresConnector("dsn")

    with patch("app.database.connector.postgres_connector.asyncpg.create_pool", new_callable=AsyncMock) as mock_pool:
        await connector.connect()

        mock_pool.assert_called_once_with(dsn="dsn")
        assert connector._pool is not None


@pytest.mark.asyncio
async def test_close_closes_pool():
    connector = PostgresConnector("dsn")
    pool = AsyncMock()
    connector._pool = pool
    
    await connector.close()
    
    pool.close.assert_awaited_once()
    assert connector._pool is None


@pytest.mark.asyncio
async def test_health_check_success():
    connector = PostgresConnector("dsn")

    connection = AsyncMock()
    connection.execute = AsyncMock()

    pool = MagicMock()
    pool.acquire.return_value.__aenter__.return_value = connection
    pool.acquire.return_value.__aexit__.return_value = None

    connector._pool = pool

    result = await connector.health_check()

    assert result is True
    connection.execute.assert_awaited_once_with("SELECT 1")


@pytest.mark.asyncio
async def test_health_check_failure():
    connector = PostgresConnector("dsn")

    connection = AsyncMock()
    connection.execute.side_effect = Exception("db error")

    pool = AsyncMock()
    pool.acquire.return_value.__aenter__.return_value = connection

    connector._pool = pool

    result = await connector.health_check()

    assert result is False


@pytest.mark.asyncio
async def test_execute_returns_rows():
    connector = PostgresConnector("dsn")

    connection = AsyncMock()
    connection.fetch = AsyncMock(return_value=[{"id": 1}])

    pool = MagicMock()
    pool.acquire.return_value.__aenter__.return_value = connection
    pool.acquire.return_value.__aexit__.return_value = None

    connector._pool = pool

    result = await connector.execute("SELECT 1")

    assert result == [{"id": 1}]
    connection.fetch.assert_awaited_once_with("SELECT 1")


@pytest.mark.asyncio
async def test_execute_not_connected():
    connector = PostgresConnector("dsn")

    with pytest.raises(DataSourceExecutionError):
        await connector.execute("SELECT 1")


@pytest.mark.asyncio
async def test_execute_exception_wrapped():
    connector = PostgresConnector("dsn")

    connection = AsyncMock()
    connection.fetch.side_effect = Exception("sql error")

    pool = AsyncMock()
    pool.acquire.return_value.__aenter__.return_value = connection

    connector._pool = pool

    with pytest.raises(DataSourceExecutionError):
        await connector.execute("SELECT 1")


@pytest.mark.asyncio
async def test_introspect_schema():
    connector = PostgresConnector("dsn")

    connection = AsyncMock()

    connection.fetch = AsyncMock(side_effect=[
        [{"table_name": "users"}],  # tables
        [
            {"column_name": "id", "data_type": "integer", "is_nullable": "NO"},
            {"column_name": "name", "data_type": "text", "is_nullable": "YES"},
        ],  # columns
        [
            {"column_name": "role_id", "ref_table": "roles", "ref_column": "id"}
        ],  # foreign keys
    ])

    pool = MagicMock()
    pool.acquire.return_value.__aenter__.return_value = connection
    pool.acquire.return_value.__aexit__.return_value = None

    connector._pool = pool

    result = await connector.introspect_schema()

    assert result["tables"][0]["name"] == "users"
    assert result["tables"][0]["columns"][0]["name"] == "id"
    assert result["tables"][0]["foreign_keys"][0]["ref_table"] == "roles"


@pytest.mark.asyncio
async def test_introspect_schema_not_connected():
    connector = PostgresConnector("dsn")

    with pytest.raises(DataSourceExecutionError):
        await connector.introspect_schema()
