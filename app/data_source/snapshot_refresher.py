from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data_source.models.schema_snapshot import SchemaSnapshotModel
from app.db_registry.database_registry import DatabaseRegistry


class SnapshotRefresher:
    """
    Admin/maintenance flow only.
    Never called during user query execution.
    """

    async def refresh(self, session: AsyncSession, data_source_id: str) -> int:
        registry = DatabaseRegistry.get_instance()
        handle = registry.get(data_source_id)
        if not handle:
            raise RuntimeError(f"Unknown data_source_id={data_source_id}")

        raw = await handle.connector.introspect_schema()

        # IMPORTANT: normalize raw introspection into the snapshot format your SchemaTransformer expects
        # If your connectors already return normalized format, keep as-is.
        snapshot = self._normalize(raw, dialect=handle.dialect)

        # version bump
        stmt = select(func.max(SchemaSnapshotModel.version)).where(
            SchemaSnapshotModel.data_source_id == data_source_id
        )
        response = await session.execute(stmt)
        max_version = response.scalar() or 0
        new_version = max_version + 1

        session.add(
            SchemaSnapshotModel(
                data_source_id=data_source_id, version=new_version, snapshot=snapshot
            )
        )
        await session.commit()

        return new_version

    def _normalize(self, raw: list[dict[str, Any]], dialect: str) -> dict:
        """
        Output must match your snapshot format:
        {
          "tables": [{ "name":..., "columns":[{name,data_type,is_nullable}], "foreign_keys":[{column,ref_table,ref_column}] }]
        }
        """
        # If raw is already in that format, just return it:
        if isinstance(raw, list):
            return {"tables": raw}

        # Otherwise, implement mapping based on how your connectors return introspection.
        # For now, keep it strict:
        raise RuntimeError(
            "Introspection output not normalized; implement _normalize() mapping."
        )
