import uuid
from typing import Any

from sqlalchemy import desc, select

from app.data_source.models.schema_snapshot import SchemaSnapshotModel
from app.data_source.session import AsyncSessionLocal


class SnapshotManager:
    """
    Layer 1 Snapshot Manager.

    Responsibilities:
    - Load latest snapshot from App DB
    - Cache snapshots in memory
    - Avoid runtime schema introspection
    """

    def __init__(self) -> None:
        self._cache: dict[str, dict[str, Any]] = {}

    async def get_snapshot(self, data_source_id: str) -> dict[str, Any]:
        # In-memory cache
        if data_source_id in self._cache:
            return self._cache[data_source_id]

        async with AsyncSessionLocal() as session:
            stmt = (
                select(SchemaSnapshotModel)
                .where(SchemaSnapshotModel.data_source_id == uuid.UUID(data_source_id))
                .order_by(desc(SchemaSnapshotModel.version))
                .limit(1)
            )
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()

        if not row:
            raise RuntimeError(
                f"No schema snapshot found for data_source_id={data_source_id}"
            )

        self._cache[data_source_id] = row.snapshot

        return row.snapshot

    def invalidate(self, data_source_id: str) -> None:
        self._cache.pop(data_source_id, None)
