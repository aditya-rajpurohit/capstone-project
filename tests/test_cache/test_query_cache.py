import time
from app.cache.query_cache import QueryCache


def test_cache_set_and_get():
    cache = QueryCache(default_ttl_seconds=10)

    cache.set("key", {"x": 1})

    assert cache.get("key") == {"x": 1}


def test_cache_miss():
    cache = QueryCache()

    result = cache.get("missing")

    assert result is None
    assert cache.stats()["misses"] == 1


def test_cache_expiration(monkeypatch):
    cache = QueryCache(default_ttl_seconds=10)

    fake_time = 1000
    monkeypatch.setattr(time, "time", lambda: fake_time)

    cache.set("key", {"x": 1})

    # move time forward beyond ttl
    monkeypatch.setattr(time, "time", lambda: fake_time + 20)

    assert cache.get("key") is None
    assert cache.stats()["misses"] == 1


def test_cache_invalidate():
    cache = QueryCache()

    cache.set("key", {"x": 1})
    cache.invalidate("key")

    assert cache.get("key") is None


def test_cache_invalidate_prefix():
    cache = QueryCache()

    cache.set("user:1", {"a": 1})
    cache.set("user:2", {"b": 2})
    cache.set("order:1", {"c": 3})

    cache.invalidate_prefix("user:")

    assert cache.get("user:1") is None
    assert cache.get("user:2") is None
    assert cache.get("order:1") == {"c": 3}


def test_cache_stats_hits():
    cache = QueryCache()

    cache.set("key", {"x": 1})
    cache.get("key")

    stats = cache.stats()

    assert stats["hits"] == 1
