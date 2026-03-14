import uuid
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.metadata.models.schema_snapshot import SchemaSnapshotModel
from app.database.registry.database_registry import DatabaseRegistry



class SnapshotRefresher:
    """
    Admin/maintenance flow only.
    Never called during user query execution.
    """

    async def refresh(self, session: AsyncSession, data_source_id: str) -> int:
        registry = DatabaseRegistry.get_instance()
        handle = registry.get(data_source_id)
        if not handle:
            raise RuntimeError(f"ERROR: Unknown data_source_id={data_source_id}")

        raw_snapshot = await handle.connector.introspect_schema()

        snapshot = self._normalize(raw_snapshot)

        ds_uuid = uuid.UUID(data_source_id)

        stmt = select(func.max(SchemaSnapshotModel.version)).where(
            SchemaSnapshotModel.data_source_id == ds_uuid
        )
        response = await session.execute(stmt)
        max_version = response.scalar() or 0
        new_version = int(max_version) + 1

        session.add(
            SchemaSnapshotModel(
                data_source_id=ds_uuid,
                version=new_version,
                snapshot=snapshot,
            )
        )
        await session.commit()
        
        return new_version

    def _normalize(self, raw: Any) -> dict[str, Any]:
        """
        Enforce canonical snapshot shape:
        {"tables": [...]}
        """
        if isinstance(raw, dict) and "tables" in raw:
            return raw
        raise RuntimeError("ERROR: Connector introspection must return {'tables': [...]} canonical snapshot.")
