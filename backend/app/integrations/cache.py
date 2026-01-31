from cachetools import TTLCache
from typing import Any, Optional

from app.config import get_settings

settings = get_settings()

# Global cache instance
_cache: Optional[TTLCache] = None


def get_cache() -> TTLCache:
    """Get or create global cache instance."""
    global _cache
    if _cache is None:
        _cache = TTLCache(maxsize=1000, ttl=settings.cache_ttl_seconds)
    return _cache


def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    cache = get_cache()
    return cache.get(key)


def cache_set(key: str, value: Any) -> None:
    """Set value in cache."""
    cache = get_cache()
    cache[key] = value


def cache_clear() -> None:
    """Clear all cached values."""
    cache = get_cache()
    cache.clear()
