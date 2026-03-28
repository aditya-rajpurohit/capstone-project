from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.snowflake_connector import SnowflakeConnector


@pytest.mark.asyncio
async def test_connect():
    with patch(
        "app.database.connectors.snowflake_connector.snowflake.connector.connect"
    ) as mock_connect:

        conn = MagicMock()
        mock_connect.return_value = conn

        connector = SnowflakeConnector("user", "pass", "acct", "db", "wh")

        await connector.connect()

        assert connector._conn == conn


@pytest.mark.asyncio
async def test_close():
    connector = SnowflakeConnector("user", "pass", "acct", "db", "wh")

    conn = MagicMock()
    connector._conn = conn

    await connector.close()

    conn.close.assert_called_once()


@pytest.mark.asyncio
async def test_execute():
    connector = SnowflakeConnector("user", "pass", "acct", "db", "wh")

    cursor = MagicMock()
    cursor.fetchall.return_value = [(1,)]
    cursor.description = [("id",)]

    conn = MagicMock()
    conn.cursor.return_value = cursor

    connector._conn = conn

    result = await connector.execute("SELECT 1")

    assert result == [{"id": 1}]


@pytest.mark.asyncio
async def test_execute_not_connected():
    connector = SnowflakeConnector("user", "pass", "acct", "db", "wh")

    with pytest.raises(DataSourceExecutionError):
        await connector.execute("SELECT 1")


@pytest.mark.asyncio
async def test_introspect_schema():
    connector = SnowflakeConnector("user", "pass", "acct", "db", "wh")

    tables_cursor = MagicMock()
    tables_cursor.fetchall.return_value = [("users",)]
    tables_cursor.description = [("TABLE_NAME",)]

    columns_cursor = MagicMock()
    columns_cursor.fetchall.return_value = [("id", "INTEGER")]
    columns_cursor.description = [("COLUMN_NAME",), ("DATA_TYPE",)]

    conn = MagicMock()
    conn.cursor.side_effect = [tables_cursor, columns_cursor]

    connector._conn = conn

    result = await connector.introspect_schema()

    assert result["tables"][0]["name"] == "users"
