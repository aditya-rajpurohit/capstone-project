from unittest.mock import MagicMock

import pytest

from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.duckdb_connector import DuckDBConnector


@pytest.mark.asyncio
async def test_connect(monkeypatch):
    mock_conn = MagicMock()

    monkeypatch.setattr(
        "app.database.connectors.duckdb_connector.duckdb.connect",
        lambda _: mock_conn,
    )

    connector = DuckDBConnector("test.db")

    await connector.connect()

    assert connector._conn == mock_conn


@pytest.mark.asyncio
async def test_close():
    connector = DuckDBConnector("test.db")

    conn = MagicMock()
    connector._conn = conn

    await connector.close()

    conn.close.assert_called_once()


@pytest.mark.asyncio
async def test_execute():
    connector = DuckDBConnector("test.db")

    cursor = MagicMock()
    cursor.fetchall.return_value = [(1,)]
    cursor.description = [("id",)]

    conn = MagicMock()
    conn.execute.return_value = cursor

    connector._conn = conn

    result = await connector.execute("SELECT 1")

    assert result == [{"id": 1}]


@pytest.mark.asyncio
async def test_execute_not_connected():
    connector = DuckDBConnector("test.db")

    with pytest.raises(DataSourceExecutionError):
        await connector.execute("SELECT 1")


@pytest.mark.asyncio
async def test_introspect_schema():
    connector = DuckDBConnector("test.db")

    tables_cursor = MagicMock()
    tables_cursor.fetchall.return_value = [("users",)]
    tables_cursor.description = [("name",)]

    columns_cursor = MagicMock()
    columns_cursor.fetchall.return_value = [(0, "id", "INTEGER")]
    columns_cursor.description = [("cid",), ("name",), ("type",)]

    conn = MagicMock()
    conn.execute.side_effect = [tables_cursor, columns_cursor]

    connector._conn = conn

    result = await connector.introspect_schema()

    assert result["tables"][0]["name"] == "users"
