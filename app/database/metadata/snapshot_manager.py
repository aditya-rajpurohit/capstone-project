import uuid
from typing import Any, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database.metadata.models.schema_snapshot import SchemaSnapshotModel
from app.database.metadata.session import get_async_session


class SnapshotManager:
    """
    Layer 1 Snapshot Manager.

    Responsibilities:
    - Load latest snapshot from App DB
    - Cache snapshots in memory
    - Avoid runtime schema introspection
    """

    def __init__(
        self, sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None
    ) -> None:
        self._cache: dict[str, dict[str, Any]] = {}
        self._Session = sessionmaker or get_async_session()

    def invalidate(self, data_source_id: str) -> None:
        self._cache.pop(data_source_id, None)

    async def get_snapshot(self, data_source_id: str) -> dict[str, Any]:
        if data_source_id in self._cache:
            return self._cache[data_source_id]

        async with self._Session() as session:
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
