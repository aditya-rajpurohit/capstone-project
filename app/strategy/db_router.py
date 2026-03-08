import re

from app.db_registry.database_registry import DatabaseRegistry


class DBRouter:
    """
    Deterministic MVP routing:
    - If user mentions a db name/alias: route to that
    - Else: return all active DBs
    """

    @staticmethod
    def route(user_query: str, active_database_ids: list[str], registry) -> list[str]:
        q = user_query.lower()
        # Match by registry handle.name (if you store it) OR db_id substring
        matched = []
        for db_id in active_database_ids:
            unit = registry.get(db_id)
            if not unit:
                continue
            name = getattr(unit, "name", "") or ""
            if name and re.search(rf"\b{re.escape(name.lower())}\b", q):
                matched.append(db_id)
            elif re.search(rf"\b{re.escape(db_id.lower())}\b", q):
                matched.append(db_id)

        return matched if matched else active_database_ids
