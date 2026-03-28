from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.mongodb_connector import MongoDBConnector


@pytest.mark.asyncio
async def test_connect():

    with patch(
        "app.database.connectors.mongodb_connector.AsyncIOMotorClient"
    ) as mock_client:

        connector = MongoDBConnector("fake_uri", "db")

        await connector.connect()

        assert connector._client is not None


@pytest.mark.asyncio
async def test_health_check():

    connector = MongoDBConnector("fake_uri", "db")

    client = AsyncMock()
    client.admin.command = AsyncMock()

    connector._client = client

    result = await connector.health_check()

    assert result is True


@pytest.mark.asyncio
async def test_execute():

    connector = MongoDBConnector("fake_uri", "db")

    docs = [{"id": 1}]

    cursor = MagicMock()
    cursor.__aiter__.return_value = docs

    collection = MagicMock()
    collection.find.return_value = cursor

    db = MagicMock()
    db.__getitem__.return_value = collection

    connector._db = db

    query = '{"collection":"users"}'

    result = await connector.execute(query)

    assert result == docs


@pytest.mark.asyncio
async def test_execute_not_connected():

    connector = MongoDBConnector("fake_uri", "db")

    with pytest.raises(DataSourceExecutionError):
        await connector.execute("{}")
