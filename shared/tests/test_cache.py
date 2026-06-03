"""Cache helper tests — verify graceful degradation when Redis misbehaves.

We swap in a fake client that raises, so we exercise the error branches without
needing a live Redis.
"""

import pytest

from shared.cache import Cache


class RaisingClient:
    async def get(self, *a, **k):
        raise ConnectionError("down")

    async def set(self, *a, **k):
        raise ConnectionError("down")

    async def delete(self, *a, **k):
        raise ConnectionError("down")

    async def aclose(self):
        return None


class RecordingClient:
    def __init__(self):
        self.store = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None):
        self.store[key] = value

    async def delete(self, *keys):
        for k in keys:
            self.store.pop(k, None)

    async def aclose(self):
        return None


@pytest.fixture
def cache():
    c = Cache("redis://localhost:6379/0")
    return c


async def test_get_returns_none_on_error(cache):
    cache.client = RaisingClient()
    assert await cache.get_json("k") is None


async def test_set_and_invalidate_swallow_errors(cache):
    cache.client = RaisingClient()
    await cache.set_json("k", {"a": 1})  # must not raise
    await cache.invalidate("k")  # must not raise


async def test_roundtrip_with_working_client(cache):
    cache.client = RecordingClient()
    await cache.set_json("k", {"a": 1})
    assert await cache.get_json("k") == {"a": 1}
    await cache.invalidate("k")
    assert await cache.get_json("k") is None


async def test_invalidate_noop_when_no_keys(cache):
    cache.client = RecordingClient()
    await cache.invalidate()  # no keys -> no-op
