from typing import Any


class SchemaSelector:
    """
    Deterministic schema selector for Layer 1.

    For now:
    - Returns full schema.
    - Later: will compress and select relevant tables.
    """

    @staticmethod
    def select(schema_snapshot: dict[str, Any], user_query: str) -> dict[str, Any]:
        # expected behavior: return full schema
        return schema_snapshot
