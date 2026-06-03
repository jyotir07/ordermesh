"""Redis cache-aside helper.

Cache failures never break the request path — they are logged and treated as a
miss / no-op so the platform degrades gracefully if Redis is unavailable.
"""

import json
import logging
from typing import Any

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class Cache:
    def __init__(self, url: str, default_ttl: int = 300) -> None:
        self.client = redis.from_url(url, decode_responses=True)
        self.default_ttl = default_ttl

    async def get_json(self, key: str) -> Any | None:
        try:
            raw = await self.client.get(key)
            return json.loads(raw) if raw is not None else None
        except Exception as exc:  # noqa: BLE001 - degrade gracefully
            logger.warning("cache get failed for %s: %s", key, exc)
            return None

    async def set_json(self, key: str, value: Any, ttl: int | None = None) -> None:
        try:
            await self.client.set(key, json.dumps(value, default=str), ex=ttl or self.default_ttl)
        except Exception as exc:  # noqa: BLE001
            logger.warning("cache set failed for %s: %s", key, exc)

    async def invalidate(self, *keys: str) -> None:
        try:
            if keys:
                await self.client.delete(*keys)
        except Exception as exc:  # noqa: BLE001
            logger.warning("cache invalidate failed: %s", exc)

    async def close(self) -> None:
        await self.client.aclose()
