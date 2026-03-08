import time
from typing import Any, Optional


class QueryCache:
    """
    Simple in-memory TTL cache.
    Keyed by:
        data_source_id + normalized_sql
    """

    def __init__(self, default_ttl_seconds: int = 300) -> None:
        self.default_ttl = default_ttl_seconds
        self._store: dict[str, dict[str, Any]] = {}

    def set(
        self, key: str, value: dict[str, Any], ttl_seconds: Optional[int] = None
    ) -> None:
        ttl = ttl_seconds or self.default_ttl
        self._store[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
        }

    def get(self, key: str) -> Optional[dict[str, Any]]:
        entry = self._store.get(key)
        if not entry:
            return None

        if time.time() > entry["expires_at"]:
            del self._store[key]
            return None

        return entry["value"]

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)
