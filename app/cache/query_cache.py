import time
from typing import Any, Optional


class QueryCache:
    """
    In-memory TTL cache.

    Key should already include:
        data_source_id + snapshot_version + normalized_sql
    """

    def __init__(self, default_ttl_seconds: int = 300) -> None:
        self.default_ttl = default_ttl_seconds
        self._store: dict[str, dict[str, Any]] = {}
        self._hits = 0
        self._misses = 0

    def set(self, key: str, value: dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        self._store[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
        }

    def get(self, key: str) -> Optional[dict[str, Any]]:
        entry = self._store.get(key)
        if not entry:
            self._misses += 1
            return None

        if time.time() > entry["expires_at"]:
            self._store.pop(key, None)
            self._misses += 1
            return None

        self._hits += 1
        return entry["value"]

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> None:
        """
        Useful for invalidating all keys of a data source.
        """
        keys_to_delete = [k for k in self._store if k.startswith(prefix)]
        for k in keys_to_delete:
            del self._store[k]

    def stats(self) -> dict[str, int]:
        return {"hits": self._hits, "misses": self._misses}
