import re

from app.database.registry.database_registry import DatabaseRegistry


class DBRouter:
    """
    Deterministic MVP routing:
    - If user mentions a db name/alias: route to that
    - Else: return all active DBs
    """

    @staticmethod
    def route(
        user_query: str, active_database_ids: list[str], registry: DatabaseRegistry
    ) -> list[str]:
        q = user_query.lower()
        matched = []

        for db_id in active_database_ids:
            unit = registry.get(db_id)
            if not unit:
                continue

            name = (unit.name or "").lower()

            if name and re.search(rf"\b{re.escape(name)}\b", q):
                matched.append(db_id)
                continue

            if re.search(rf"\b{re.escape(db_id.lower())}\b", q):
                matched.append(db_id)

        return matched if matched else active_database_ids
