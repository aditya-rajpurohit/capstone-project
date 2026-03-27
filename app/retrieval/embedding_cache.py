import hashlib


class EmbeddingCache:
    def __init__(self) -> None:
        self._cache: dict[str, list[float]] = {}

    @staticmethod
    def _key(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get(self, text: str) -> list[float] | None:
        return self._cache.get(self._key(text))

    def set(self, text: str, embedding: list[float]) -> None:
        self._cache[self._key(text)] = embedding
