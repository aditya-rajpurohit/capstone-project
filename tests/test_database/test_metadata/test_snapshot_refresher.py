# RUN THIS
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.database.metadata.snapshot_refresher import SnapshotRefresher


@pytest.mark.asyncio
async def test_refresh_success():
    refresher = SnapshotRefresher()

    raw_snapshot = {"tables": [{"name": "users", "columns": [], "foreign_keys": []}]}

    connector = AsyncMock()
    connector.introspect_schema.return_value = raw_snapshot

    handle = MagicMock()
    handle.connector = connector

    registry = MagicMock()
    registry.get.return_value = handle

    response = MagicMock()
    response.scalar.return_value = 2  # existing max version

    session = AsyncMock()
    session.execute.return_value = response

    data_source_id = "12345678-1234-5678-1234-567812345678"

    with patch(
        "app.database.metadata.snapshot_refresher.DatabaseRegistry.get_instance",
        return_value=registry,
    ):
        version = await refresher.refresh(session, data_source_id)

    assert version == 3
    connector.introspect_schema.assert_awaited_once()
    session.execute.assert_awaited_once()
    session.add.assert_called_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_unknown_data_source():
    refresher = SnapshotRefresher()

    registry = MagicMock()
    registry.get.return_value = None

    session = AsyncMock()

    with patch(
        "app.database.metadata.snapshot_refresher.DatabaseRegistry.get_instance",
        return_value=registry,
    ):
        with pytest.raises(RuntimeError, match="Unknown data_source_id"):
            await refresher.refresh(session, "12345678-1234-5678-1234-567812345678")


def test_normalize_valid_snapshot():
    refresher = SnapshotRefresher()

    snapshot = {"tables": []}

    result = refresher._normalize(snapshot)

    assert result == snapshot


def test_normalize_invalid_snapshot():
    refresher = SnapshotRefresher()

    with pytest.raises(RuntimeError, match="Connector introspection must return"):
        refresher._normalize({"bad": "data"})
