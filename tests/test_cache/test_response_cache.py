import time
from app.cache.response_cache import ResponseCache


def test_response_cache_set_and_get():
    cache = ResponseCache(ttl_seconds=10)

    key = cache.build_key("openai", "gpt", "sys", "user", "Schema", 0, 1)
    cache.set(key, {"a": 1})

    assert cache.get(key) == {"a": 1}


def test_build_key_is_deterministic():
    key1 = ResponseCache.build_key("openai", "gpt", "sys", "user", "Schema", 0, 1)
    key2 = ResponseCache.build_key("openai", "gpt", "sys", "user", "Schema", 0, 1)

    assert key1 == key2


def test_cache_miss():
    cache = ResponseCache()

    assert cache.get("missing") is None


def test_cache_expiration(monkeypatch):
    cache = ResponseCache(ttl_seconds=10)

    fake_time = 1000
    monkeypatch.setattr(time, "time", lambda: fake_time)

    key = cache.build_key("openai", "gpt", "sys", "user", None, 0, 1)
    cache.set(key, {"x": 1})

    # move time forward past ttl
    monkeypatch.setattr(time, "time", lambda: fake_time + 20)

    assert cache.get(key) is None


def test_invalidate_all():
    cache = ResponseCache()

    key1 = cache.build_key("p", "m", "s", "u", None, 0, 1)
    key2 = cache.build_key("p2", "m2", "s2", "u2", None, 0, 1)

    cache.set(key1, {"a": 1})
    cache.set(key2, {"b": 2})

    cache.invalidate_all()

    assert cache.get(key1) is None
    assert cache.get(key2) is None
