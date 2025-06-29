import pytest
import time
from src.uckn.core.atoms.semantic_search_engine_optimized import (
    SemanticSearchEngineOptimized,
    CacheManager,
)
from src.uckn.core.atoms.multi_modal_embeddings_optimized import MultiModalEmbeddingsOptimized

def test_cache_benchmark():
    cache = CacheManager(max_size=100)
    for i in range(200):
        cache.set(f"key{i}", i)
    # Only 100 should remain
    assert len(cache.cache) == 100

def test_embedding_batch_performance():
    embeddings = MultiModalEmbeddingsOptimized()
    items = [f"item {i}" for i in range(1000)]
    start = time.time()
    result = embeddings.embed_batch(items)
    elapsed = time.time() - start
    assert len(result) == 1000
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
