from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.cassandra_connector import CassandraConnector


@pytest.mark.asyncio
async def test_connect():
    with patch("app.database.connectors.cassandra_connector.Cluster") as mock_cluster:

        cluster = MagicMock()
        session = MagicMock()

        mock_cluster.return_value = cluster
        cluster.connect.return_value = session

        connector = CassandraConnector(["localhost"], "test")

        await connector.connect()

        assert connector._session == session


@pytest.mark.asyncio
async def test_close():
    connector = CassandraConnector(["localhost"], "test")

    cluster = MagicMock()
    connector._cluster = cluster

    await connector.close()

    cluster.shutdown.assert_called_once()


@pytest.mark.asyncio
async def test_execute():
    connector = CassandraConnector(["localhost"], "test")

    rows = [MagicMock(_asdict=lambda: {"id": 1})]

    session = MagicMock()
    session.execute.return_value = rows

    connector._session = session

    result = await connector.execute("SELECT * FROM users")

    assert result == [{"id": 1}]


@pytest.mark.asyncio
async def test_execute_not_connected():
    connector = CassandraConnector(["localhost"], "test")

    with pytest.raises(DataSourceExecutionError):
        await connector.execute("SELECT 1")


@pytest.mark.asyncio
async def test_introspect_schema():
    connector = CassandraConnector(["localhost"], "test")

    rows = [MagicMock(table_name="users")]

    session = MagicMock()
    session.execute.return_value = rows

    connector._session = session

    result = await connector.introspect_schema()

    assert result["tables"][0]["name"] == "users"
