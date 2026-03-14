import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from app.database.execution.execution_engine import ExecutionEngine
from app.core.exceptions import DataSourceExecutionError


@pytest.mark.asyncio
async def test_execute_success():
    connector = AsyncMock()
    connector.execute.return_value = [{"id": 1}, {"id": 2}]

    engine = ExecutionEngine(connector)

    result = await engine.execute("SELECT * FROM users")

    assert result.status == "success"
    assert result.rows == [{"id": 1}, {"id": 2}]
    assert result.row_count == 2
    if result.elapsed_ms:
        assert result.elapsed_ms >= 0


@pytest.mark.asyncio
async def test_execute_timeout():
    connector = AsyncMock()
    engine = ExecutionEngine(connector)

    with patch(
        "app.database.execution.execution_engine.asyncio.wait_for",
        new=AsyncMock(side_effect=asyncio.TimeoutError)
    ):
        result = await engine.execute("SELECT 1")

    assert result.status == "failed"
    assert result.error_type == "timeout"
    assert result.error_message == "Query execution exceeded timeout."


@pytest.mark.asyncio
async def test_execute_datasource_error():
    connector = AsyncMock()
    connector.execute.side_effect = DataSourceExecutionError("db error")

    engine = ExecutionEngine(connector)

    result = await engine.execute("SELECT 1")

    assert result.status == "failed"
    assert result.error_type == "datasource_error"
    assert result.error_message == "db error"


@pytest.mark.asyncio
async def test_execute_unknown_error():
    connector = AsyncMock()
    connector.execute.side_effect = Exception("unexpected")

    engine = ExecutionEngine(connector)

    result = await engine.execute("SELECT 1")

    assert result.status == "failed"
    assert result.error_type == "unknown_error"
    assert result.error_message == "unexpected"
