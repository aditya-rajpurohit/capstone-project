from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.redis_connector import RedisConnector


@pytest.mark.asyncio
async def test_connect():

    with patch("app.database.connectors.redis_connector.redis.from_url") as mock_client:
        connector = RedisConnector("redis://fake")

        await connector.connect()

        mock_client.assert_called_once()


@pytest.mark.asyncio
async def test_health_check():

    connector = RedisConnector("redis://fake")

    client = AsyncMock()
    client.ping.return_value = True

    connector._client = client

    result = await connector.health_check()

    assert result is True


@pytest.mark.asyncio
async def test_execute_get():

    connector = RedisConnector("redis://fake")

    client = AsyncMock()
    client.get.return_value = "value"

    connector._client = client

    result = await connector.execute("get key")

    assert result == [{"value": "value"}]


@pytest.mark.asyncio
async def test_execute_not_connected():

    connector = RedisConnector("redis://fake")

    with pytest.raises(DataSourceExecutionError):
        await connector.execute("get key")
