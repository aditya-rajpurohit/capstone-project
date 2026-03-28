from app.retrieval.embedding_cache import EmbeddingCache


def test_embedding_cache_set_and_get():
    cache = EmbeddingCache()

    cache.set("text", [0.1, 0.2])

    assert cache.get("text") == [0.1, 0.2]


def test_embedding_cache_miss():
    cache = EmbeddingCache()

    assert cache.get("unknown") is None
