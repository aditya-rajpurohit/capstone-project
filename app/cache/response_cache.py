import hashlib
import time
from typing import Any, Optional


class ResponseCache:
    """
    Caches structured model responses.
    """
    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl = ttl_seconds
        self._store: dict[str, dict[str, Any]] = {}

    @staticmethod
    def build_key(provider: str, model: str, system_prompt: str, user_prompt: str, schema_name: Optional[str], temperature: float, top_p: float) -> str:
        raw = (
            f"{provider}|{model}|{schema_name}|"
            f"{temperature}|{top_p}|"
            f"{system_prompt}|{user_prompt}"
        )

        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        item = self._store.get(key)
        if not item:
            return None

        if time.time() > item["expires_at"]:
            self._store.pop(key, None)
            return None

        return item["value"]
    
    def set(self, key: str, value: Any) -> None:
        self._store[key] = {
            "value": value,
            "expires_at": time.time() + self.ttl,
        }

    def invalidate_all(self) -> None:
        self._store.clear()
