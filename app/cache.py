import hashlib
import os
from functools import lru_cache
from typing import Optional
from upstash_redis import Redis

# cache TTL setting (1 hour default)
CACHE_TTL_SECONDS = int(os.getenv("RESPONSE_CACHE_TTL_SECONDS", "3600"))


@lru_cache(maxsize=1)

def _get_client() -> Redis:
    return Redis.from_env()


def _cache_key(message: str) -> str:
# simple sha256 hash of normalized text string
    normalized = message.strip().lower()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"cache:response:{digest}"


def get_cached_response(message: str) -> Optional[str]:
    return _get_client().get(_cache_key(message))


def set_cached_response(message: str, response: str, ttl: int = CACHE_TTL_SECONDS) -> None:
    _get_client().set(_cache_key(message), response, ex=ttl)