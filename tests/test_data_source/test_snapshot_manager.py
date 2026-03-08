import pytest

from app.data_source.snapshot_manager import SnapshotManager


@pytest.mark.asyncio
async def test_get_snapshot():

    snapshot_manager = SnapshotManager()

    # manually inject cache
    snapshot_manager._cache["x"] = {"tables": []}

    snapshot = await snapshot_manager.get_snapshot("x")

    assert snapshot == {"tables": []}
