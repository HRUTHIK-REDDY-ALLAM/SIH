"""Cache / session-state layer.

Uses Redis when REDIS_URL is set and reachable (the Docker Compose stack wires
this up); falls back to an in-process store so `python run.py` alone still
works. Two jobs:

1. **Auth epoch** — JWTs embed the epoch at issue time; bumping it (demo reset)
   revokes every outstanding session. This is the stateless-JWT revocation
   pattern.
2. **Deal payload cache** — finished deals are immutable between actions, so
   their serialized payloads are cached briefly and invalidated on writes.
"""
import time

from .secrets import get_secrets_provider

EPOCH_KEY = "vittsetu:auth_epoch"


class InMemoryCache:
    name = "in-memory fallback"

    def __init__(self):
        self._store: dict[str, tuple[str, float | None]] = {}

    def get(self, key: str) -> str | None:
        item = self._store.get(key)
        if item is None:
            return None
        value, expires = item
        if expires is not None and time.monotonic() > expires:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        self._store[key] = (value, time.monotonic() + ttl if ttl else None)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def incr(self, key: str) -> int:
        value = int(self.get(key) or 0) + 1
        self.set(key, str(value))
        return value


class RedisCache:
    def __init__(self, url: str):
        import redis

        self._client = redis.Redis.from_url(url, decode_responses=True,
                                            socket_connect_timeout=2, socket_timeout=2)
        self._client.ping()
        self.name = f"redis ({url.split('@')[-1]})"

    def get(self, key: str) -> str | None:
        return self._client.get(key)

    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        self._client.set(key, value, ex=ttl)

    def delete(self, key: str) -> None:
        self._client.delete(key)

    def incr(self, key: str) -> int:
        return int(self._client.incr(key))


_cache = None


def get_cache():
    global _cache
    if _cache is None:
        url = get_secrets_provider().get("REDIS_URL")
        if url:
            try:
                _cache = RedisCache(url)
            except Exception:
                _cache = InMemoryCache()
        else:
            _cache = InMemoryCache()
    return _cache


def auth_epoch() -> int:
    return int(get_cache().get(EPOCH_KEY) or 0)


def bump_auth_epoch() -> int:
    return get_cache().incr(EPOCH_KEY)


def cache_deal(deal_id: int, payload_json: str, ttl: int = 30) -> None:
    get_cache().set(f"vittsetu:deal:{deal_id}", payload_json, ttl=ttl)


def get_cached_deal(deal_id: int) -> str | None:
    return get_cache().get(f"vittsetu:deal:{deal_id}")


def invalidate_deal(deal_id: int) -> None:
    get_cache().delete(f"vittsetu:deal:{deal_id}")
