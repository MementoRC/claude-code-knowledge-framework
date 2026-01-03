import os
import time

import pytest

from src.uckn.core.atoms.multi_modal_embeddings_optimized import (
    MultiModalEmbeddingsOptimized,
)
from src.uckn.core.atoms.semantic_search_engine_optimized import (
    CacheManager,
    SemanticSearchEngineOptimized,
)

# CI detection
IS_CI = os.getenv("CI") == "1" or os.getenv("ENVIRONMENT") == "ci"


def test_cache_benchmark():
    cache = CacheManager(max_size=100)
    # Use smaller range in CI for faster execution
    iterations = 50 if IS_CI else 200
    for i in range(iterations):
        cache.set(f"key{i}", i)
    # Only 100 should remain (or 50 in CI)
    expected_size = min(iterations, 100)
    assert len(cache.cache) == expected_size


@pytest.mark.skipif(IS_CI, reason="Performance test skipped in CI")
def test_embedding_batch_performance():
    embeddings = MultiModalEmbeddingsOptimized()
    # Use smaller batch in CI
    batch_size = 100 if IS_CI else 1000
    items = [f"item {i}" for i in range(batch_size)]
    start = time.time()
    result = embeddings.embed_batch(items)
    elapsed = time.time() - start
    assert len(result) == batch_size
    assert elapsed < 5  # Should be fast


def test_search_latency(monkeypatch):
    class DummyChroma:
        def search_documents(self, **kwargs):
            time.sleep(0.01)
            return [{"id": 1}]

    engine = SemanticSearchEngineOptimized(chroma_connector=DummyChroma())
    start = time.time()
    engine.search({"text": "latency"}, "code_patterns")
    elapsed = time.time() - start
    assert elapsed < 1


def test_cache_hit_rate():
    cache = CacheManager(max_size=10)
    embeddings = MultiModalEmbeddingsOptimized(cache_manager=cache)
    for i in range(10):
        embeddings.embed(f"item {i}")
    # All should be cached
    for i in range(10):
        assert cache.get(f"auto:item {i}") is not None
