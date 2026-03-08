import hashlib
import time
from typing import Any, Optional


class ResponseCache:
    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl = ttl_seconds
        self._store: dict[str, dict[str, Any]] = {}

    @staticmethod
    def key(model: str, system_prompt: str, user_prompt: str, schema_name: str) -> str:
        raw = f"{model}::{schema_name}::{system_prompt}::{user_prompt}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[dict[str, Any]]:
        item = self._store.get(key)
        if not item:
            return None
        if time.time() > item["expires_at"]:
            self._store.pop(key, None)
            return None
        return item["value"]

    def set(self, key: str, value: dict[str, Any]) -> None:
        self._store[key] = {"value": value, "expires_at": time.time() + self.ttl}
