from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.clickhouse_connector import ClickHouseConnector


@pytest.mark.asyncio
async def test_connect():
    with patch(
        "app.database.connectors.clickhouse_connector.clickhouse_connect.get_client"
    ) as mock_client:

        client = MagicMock()
        mock_client.return_value = client

        connector = ClickHouseConnector("localhost", "db")

        await connector.connect()

        assert connector._client == client


@pytest.mark.asyncio
async def test_execute():
    connector = ClickHouseConnector("localhost", "db")

    result = MagicMock()
    result.column_names = ["id"]
    result.result_rows = [(1,)]

    client = MagicMock()
    client.query.return_value = result

    connector._client = client

    rows = await connector.execute("SELECT 1")

    assert rows == [{"id": 1}]


@pytest.mark.asyncio
async def test_execute_not_connected():
    connector = ClickHouseConnector("localhost", "db")

    with pytest.raises(DataSourceExecutionError):
        await connector.execute("SELECT 1")


@pytest.mark.asyncio
async def test_introspect_schema():
    connector = ClickHouseConnector("localhost", "db")

    tables_result = MagicMock()
    tables_result.column_names = ["name"]
    tables_result.result_rows = [("users",)]

    columns_result = MagicMock()
    columns_result.column_names = ["name", "type"]
    columns_result.result_rows = [("id", "UInt64")]

    client = MagicMock()
    client.query.side_effect = [tables_result, columns_result]

    connector._client = client

    result = await connector.introspect_schema()

    assert result["tables"][0]["name"] == "users"
