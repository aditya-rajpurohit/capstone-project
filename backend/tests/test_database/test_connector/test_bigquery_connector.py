from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.bigquery_connector import BigQueryConnector


@pytest.mark.asyncio
async def test_connect():
    with patch(
        "app.database.connectors.bigquery_connector.bigquery.Client"
    ) as mock_client:

        client = MagicMock()
        mock_client.return_value = client

        connector = BigQueryConnector("project", "dataset")

        await connector.connect()

        assert connector._client == client


@pytest.mark.asyncio
async def test_execute():
    connector = BigQueryConnector("project", "dataset")

    row = MagicMock()
    row.items.return_value = {"id": 1}.items()

    job = MagicMock()
    job.result.return_value = [row]

    client = MagicMock()
    client.query.return_value = job

    connector._client = client

    result = await connector.execute("SELECT 1")

    assert result == [{"id": 1}]


@pytest.mark.asyncio
async def test_execute_not_connected():
    connector = BigQueryConnector("project", "dataset")

    with pytest.raises(DataSourceExecutionError):
        await connector.execute("SELECT 1")


@pytest.mark.asyncio
async def test_introspect_schema():
    connector = BigQueryConnector("project", "dataset")

    table_row = MagicMock()
    table_row.items.return_value = {"table_name": "users"}.items()

    column_row = MagicMock()
    column_row.items.return_value = {
        "column_name": "id",
        "data_type": "INTEGER",
    }.items()

    job_tables = MagicMock()
    job_tables.result.return_value = [table_row]

    job_columns = MagicMock()
    job_columns.result.return_value = [column_row]

    client = MagicMock()
    client.query.side_effect = [job_tables, job_columns]

    connector._client = client

    result = await connector.introspect_schema()

    assert result["tables"][0]["name"] == "users"
