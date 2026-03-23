from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.sqlite_connector import SQLiteConnector


@pytest.mark.asyncio
async def test_connect():

    connector = SQLiteConnector("test.db")

    mock_conn = AsyncMock()

    with patch(
        "app.database.connectors.sqlite_connector.aiosqlite.connect",
        new_callable=AsyncMock,
        return_value=mock_conn,
    ):
        await connector.connect()

        assert connector._conn == mock_conn


@pytest.mark.asyncio
async def test_close():

    connector = SQLiteConnector("test.db")

    conn = AsyncMock()
    connector._conn = conn

    await connector.close()

    conn.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_health_check_success():

    connector = SQLiteConnector("test.db")

    context = AsyncMock()
    context.__aenter__.return_value = None
    context.__aexit__.return_value = None

    conn = MagicMock()
    conn.execute.return_value = context

    connector._conn = conn

    result = await connector.health_check()

    assert result is True


@pytest.mark.asyncio
async def test_execute():

    connector = SQLiteConnector("test.db")

    cursor = AsyncMock()
    cursor = AsyncMock()
    cursor.fetchall = AsyncMock(return_value=[{"id": 1}])

    context = AsyncMock()
    context.__aenter__.return_value = cursor
    context.__aexit__.return_value = None

    conn = MagicMock()
    conn.execute.return_value = context

    connector._conn = conn

    result = await connector.execute("SELECT 1")

    assert result == [{"id": 1}]


@pytest.mark.asyncio
async def test_execute_not_connected():

    connector = SQLiteConnector("test.db")

    with pytest.raises(DataSourceExecutionError):
        await connector.execute("SELECT 1")


@pytest.mark.asyncio
async def test_introspect_schema():

    connector = SQLiteConnector("test.db")

    # query 1: tables
    tables_cursor = AsyncMock()
    tables_cursor.fetchall = AsyncMock(return_value=[{"name": "users"}])

    tables_ctx = AsyncMock()
    tables_ctx.__aenter__.return_value = tables_cursor
    tables_ctx.__aexit__.return_value = None

    # query 2: columns
    columns_cursor = AsyncMock()
    columns_cursor.fetchall = AsyncMock(
        return_value=[{"name": "id", "type": "INTEGER", "notnull": 1}]
    )

    # query 3: foreign keys
    fk_cursor = AsyncMock()
    fk_cursor.fetchall = AsyncMock(return_value=[])

    conn = MagicMock()

    def execute_mock(sql):

        if "sqlite_master" in sql:
            return tables_ctx

        if "PRAGMA table_info" in sql:

            async def _columns():
                return columns_cursor

            return _columns()

        if "PRAGMA foreign_key_list" in sql:

            async def _fk():
                return fk_cursor

            return _fk()

    conn.execute = execute_mock

    connector._conn = conn

    result = await connector.introspect_schema()

    assert result["tables"][0]["name"] == "users"
