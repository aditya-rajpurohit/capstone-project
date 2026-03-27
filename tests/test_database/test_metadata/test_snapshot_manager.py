# RUN THIS
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.database.metadata.snapshot_manager import SnapshotManager


@pytest.mark.asyncio
async def test_get_snapshot_cache_hit():
    snapshot_manager = SnapshotManager()

    snapshot_manager._cache["x"] = {"tables": []}

    snapshot = await snapshot_manager.get_snapshot("x")

    assert snapshot == {"tables": []}


@pytest.mark.asyncio
async def test_get_snapshot_db_fetch():
    fake_snapshot = {"tables": [{"name": "users"}]}

    row = MagicMock()
    row.snapshot = fake_snapshot

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = row

    session = AsyncMock()
    session.execute.return_value = result_mock

    sessionmaker = MagicMock()
    sessionmaker.return_value.__aenter__.return_value = session
    sessionmaker.return_value.__aexit__.return_value = None

    snapshot_manager = SnapshotManager(sessionmaker=sessionmaker)

    snapshot = await snapshot_manager.get_snapshot(
        "12345678-1234-5678-1234-567812345678"
    )

    assert snapshot == fake_snapshot
    assert (
        snapshot_manager._cache["12345678-1234-5678-1234-567812345678"] == fake_snapshot
    )


@pytest.mark.asyncio
async def test_get_snapshot_not_found():
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None

    session = AsyncMock()
    session.execute.return_value = result_mock

    sessionmaker = MagicMock()
    sessionmaker.return_value.__aenter__.return_value = session
    sessionmaker.return_value.__aexit__.return_value = None

    snapshot_manager = SnapshotManager(sessionmaker=sessionmaker)

    with pytest.raises(RuntimeError):
        await snapshot_manager.get_snapshot("12345678-1234-5678-1234-567812345678")
