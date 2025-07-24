"""
Optimized Semantic Search Engine for UCKN

- Integrates cache manager, async processing, batch processing, resource monitoring, and analytics.
- Backward compatible with existing SemanticSearchEngine API.
- Performance mode can be enabled/disabled via config.
"""

import asyncio
import logging
import time
from functools import wraps
from typing import Any

from src.uckn.core.atoms.multi_modal_embeddings_optimized import (
    MultiModalEmbeddingsOptimized,
)


# Dummy cache manager for demonstration
class CacheManager:
    def __init__(self, max_size=256):
        self.cache = {}
        self.max_size = max_size

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        if len(self.cache) >= self.max_size:
            self.cache.pop(next(iter(self.cache)))
        self.cache[key] = value

    def clear(self):
        self.cache.clear()


# Dummy resource monitor
class ResourceMonitor:
    def __init__(self):
        self.usage = []

    def record(self, metric):
        self.usage.append((time.time(), metric))

    def get_usage(self):
        return self.usage


# Dummy analytics
class PerformanceAnalytics:
    def __init__(self):
        self.records = []

    def log(self, event, value):
        self.records.append((event, value))

    def summary(self):
        return dict(self.records)


class SemanticSearchEngineOptimized:
    """
    Optimized semantic search engine with performance features.
    """

    def __init__(
        self,
        chroma_connector: Any | None = None,
        embedding_atom: Any | None = None,
        logger: logging.Logger | None = None,
        cache_size: int = 256,
        performance_mode: bool = True,
        enable_async: bool = True,
        enable_batch: bool = True,
        enable_monitoring: bool = True,
        enable_analytics: bool = True,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.chroma_connector = chroma_connector
        self.performance_mode = performance_mode
        self.enable_async = enable_async
        self.enable_batch = enable_batch
        self.enable_monitoring = enable_monitoring
        self.enable_analytics = enable_analytics

        self.cache_manager = (
            CacheManager(max_size=cache_size) if performance_mode else None
        )
        self.resource_monitor = ResourceMonitor() if enable_monitoring else None
        self.analytics = PerformanceAnalytics() if enable_analytics else None

        self.embedding_atom = embedding_atom or MultiModalEmbeddingsOptimized(
            cache_manager=self.cache_manager,
            resource_monitor=self.resource_monitor,
            analytics=self.analytics,
        )

    def is_available(self) -> bool:
        return self.chroma_connector is not None and self.embedding_atom is not None

    def _cache_key(self, *args, **kwargs):
        return str(args) + str(kwargs)

    def _cache_result(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not self.cache_manager:
                return fn(*args, **kwargs)
            key = self._cache_key(fn.__name__, *args, **kwargs)
            cached = self.cache_manager.get(key)
            if cached is not None:
                if self.analytics:
                    self.analytics.log("cache_hit", key)
                return cached
            result = fn(*args, **kwargs)
            self.cache_manager.set(key, result)
            if self.analytics:
                self.analytics.log("cache_miss", key)
            return result

        return wrapper

    async def _async_search(self, *args, **kwargs):
        return await asyncio.to_thread(self.search, *args, **kwargs)

    def search(
        self,
        query: dict[str, str | None],
        collection_name: str,
        limit: int = 10,
        min_similarity: float = 0.7,
    ):
        start = time.time()
        embedding = self.embedding_atom.multi_modal_embed(
            code=query.get("code"),
            text=query.get("text"),
            config=query.get("config"),
            error=query.get("error"),
        )
        if embedding is None:
            self.logger.warning("Failed to generate embedding for query.")
            return []
        results = self.chroma_connector.search_documents(
            collection_name=collection_name,
            query_embedding=embedding,
            n_results=limit,
            min_similarity=min_similarity,
        )
        elapsed = time.time() - start
        if self.resource_monitor:
            self.resource_monitor.record({"search_time": elapsed})
        if self.analytics:
            self.analytics.log("search_latency", elapsed)
        return results

    def batch_search(
        self,
        queries: list[dict[str, str | None]],
        collection_name: str,
        limit: int = 10,
        min_similarity: float = 0.7,
    ):
        if not self.enable_batch:
            return [
                self.search(q, collection_name, limit, min_similarity) for q in queries
            ]
        start = time.time()
        embeddings = self.embedding_atom.multi_modal_embed_batch(queries)
        results = []
        for embedding in embeddings:
            if embedding is None:
                results.append([])
            else:
                res = self.chroma_connector.search_documents(
                    collection_name=collection_name,
                    query_embedding=embedding,
                    n_results=limit,
                    min_similarity=min_similarity,
                )
                results.append(res)
        elapsed = time.time() - start
        if self.resource_monitor:
            self.resource_monitor.record({"batch_search_time": elapsed})
        if self.analytics:
            self.analytics.log("batch_search_latency", elapsed)
        return results

    def enable_performance_mode(self, enabled: bool = True):
        self.performance_mode = enabled

    def get_performance_summary(self):
        return {
            "resource_usage": self.resource_monitor.get_usage()
            if self.resource_monitor
            else None,
            "analytics": self.analytics.summary() if self.analytics else None,
        }
