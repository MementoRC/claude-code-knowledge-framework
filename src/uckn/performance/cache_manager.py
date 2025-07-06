"""
UCKN Performance Cache Manager

- Multi-level cache: in-memory (LRU) + Redis
- Used for embeddings and search results
- TTL-based expiration, LRU eviction, cache warming/invalidation
"""

import logging
import time
import threading
from typing import Any, Optional, Callable

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False


class MemoryCache:
    """Simple thread-safe in-memory LRU cache with TTL support."""

    def __init__(self, max_size=1024, default_ttl=600):
        self.cache = {}
        self.access = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.lock = threading.Lock()

    def _evict(self):
        # Remove least recently used
        if len(self.cache) > self.max_size:
            oldest = min(self.access, key=self.access.get)
            self.cache.pop(oldest, None)
            self.access.pop(oldest, None)

    def set(self, key, value, ttl=None):
        with self.lock:
            expire_at = time.time() + (ttl or self.default_ttl)
            self.cache[key] = (value, expire_at)
            self.access[key] = time.time()
            self._evict()

    def get(self, key):
        with self.lock:
            item = self.cache.get(key)
            if not item:
                return None
            value, expire_at = item
            if expire_at < time.time():
                self.cache.pop(key, None)
                self.access.pop(key, None)
                return None
            self.access[key] = time.time()
            return value

    def invalidate(self, key):
        with self.lock:
            self.cache.pop(key, None)
            self.access.pop(key, None)

    def clear(self):
        with self.lock:
            self.cache.clear()
            self.access.clear()


class RedisCache:
    """Redis-backed cache with TTL and fallback to memory cache."""

    def __init__(
        self, host="localhost", port=6379, db=0, default_ttl=600, memory_cache=None
    ):
        self.logger = logging.getLogger(__name__)
        self.default_ttl = default_ttl
        self.memory_cache = memory_cache or MemoryCache()
        if REDIS_AVAILABLE:
            try:
                self.client = redis.StrictRedis(
                    host=host, port=port, db=db, decode_responses=False
                )
                self.client.ping()
                self.enabled = True
            except Exception as e:
                self.logger.warning(
                    f"Redis unavailable: {e}. Falling back to memory cache."
                )
                self.client = None
                self.enabled = False
        else:
            self.logger.warning("Redis not installed. Using memory cache only.")
            self.client = None
            self.enabled = False

    def set(self, key, value, ttl=None):
        if self.enabled:
            try:
                self.client.setex(key, ttl or self.default_ttl, value)
            except Exception as e:
                self.logger.error(f"Redis set failed: {e}")
                self.memory_cache.set(key, value, ttl)
        else:
            self.memory_cache.set(key, value, ttl)

    def get(self, key):
        if self.enabled:
            try:
                value = self.client.get(key)
                if value is not None:
                    return value
            except Exception as e:
                self.logger.error(f"Redis get failed: {e}")
        return self.memory_cache.get(key)

    def invalidate(self, key):
        if self.enabled:
            try:
                self.client.delete(key)
            except Exception as e:
                self.logger.error(f"Redis delete failed: {e}")
        self.memory_cache.invalidate(key)

    def clear(self):
        if self.enabled:
            try:
                self.client.flushdb()
            except Exception as e:
                self.logger.error(f"Redis flushdb failed: {e}")
        self.memory_cache.clear()


class PerformanceCacheManager:
    """
    Multi-level cache manager for UCKN performance optimization.
    - Used for embeddings, search results, etc.
    - Supports cache warming, invalidation, TTL, and LRU.
    """

    def __init__(
        self,
        max_size=2048,
        default_ttl=900,
        redis_host="localhost",
        redis_port=6379,
        redis_db=0,
    ):
        self.memory_cache = MemoryCache(max_size=max_size, default_ttl=default_ttl)
        self.redis_cache = RedisCache(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            default_ttl=default_ttl,
            memory_cache=self.memory_cache,
        )
        self.logger = logging.getLogger(__name__)

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        self.redis_cache.set(key, value, ttl)

    def get(self, key: str) -> Any:
        return self.redis_cache.get(key)

    def invalidate(self, key: str):
        self.redis_cache.invalidate(key)

    def clear(self):
        self.redis_cache.clear()

    def cache_warm(
        self, keys: list, fetch_fn: Callable[[str], Any], ttl: Optional[int] = None
    ):
        """Pre-populate cache for a list of keys using fetch_fn."""
        for key in keys:
            if self.get(key) is None:
                value = fetch_fn(key)
                if value is not None:
                    self.set(key, value, ttl)

    def cache_invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching a pattern (Redis only)."""
        if self.redis_cache.enabled:
            try:
                for key in self.redis_cache.client.scan_iter(pattern):
                    self.redis_cache.client.delete(key)
            except Exception as e:
                self.logger.error(f"Pattern invalidation failed: {e}")


# Singleton for global cache manager
performance_cache = PerformanceCacheManager()
