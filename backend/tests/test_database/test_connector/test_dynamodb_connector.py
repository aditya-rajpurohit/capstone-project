from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.dynamodb_connector import DynamoDBConnector


@pytest.mark.asyncio
async def test_connect():
    connector = DynamoDBConnector("us-east-1")

    with patch(
        "app.database.connectors.dynamodb_connector.aioboto3.Session"
    ) as mock_session:

        session = MagicMock()
        client = AsyncMock()

        mock_session.return_value = session
        session.client.return_value.__aenter__.return_value = client

        await connector.connect()

        assert connector._client == client


@pytest.mark.asyncio
async def test_close():
    connector = DynamoDBConnector("us-east-1")

    client = AsyncMock()
    connector._client = client

    await connector.close()

    client.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
async def test_health_check_success():
    connector = DynamoDBConnector("us-east-1")

    client = AsyncMock()
    client.list_tables = AsyncMock(return_value={"TableNames": []})

    connector._client = client

    result = await connector.health_check()

    assert result is True


@pytest.mark.asyncio
async def test_execute():
    connector = DynamoDBConnector("us-east-1")

    client = AsyncMock()

    client.get_item = AsyncMock(return_value={"Item": {"id": {"S": "1"}}})

    connector._client = client

    query = '{"table":"users","key":{"id":{"S":"1"}}}'

    result = await connector.execute(query)

    assert result == [{"id": {"S": "1"}}]


@pytest.mark.asyncio
async def test_execute_not_connected():
    connector = DynamoDBConnector("us-east-1")

    with pytest.raises(DataSourceExecutionError):
        await connector.execute("{}")


@pytest.mark.asyncio
async def test_introspect_schema():
    connector = DynamoDBConnector("us-east-1")

    client = AsyncMock()
    client.list_tables = AsyncMock(return_value={"TableNames": ["users"]})

    connector._client = client

    result = await connector.introspect_schema()

    assert result["tables"][0]["name"] == "users"
