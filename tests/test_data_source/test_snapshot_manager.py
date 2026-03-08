import pytest

from app.data_source.snapshot_manager import SnapshotManager


@pytest.mark.asyncio
async def test_get_snapshot():

    sm = SnapshotManager()

    # manually inject cache
    sm._cache["x"] = {"tables": []}

    snapshot = await sm.get_snapshot("x")

    assert snapshot == {"tables": []}
