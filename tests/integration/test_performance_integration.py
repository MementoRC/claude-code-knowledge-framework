import pytest
from src.uckn.core.atoms.semantic_search_engine_optimized import (
    SemanticSearchEngineOptimized,
    CacheManager,
    ResourceMonitor,
    PerformanceAnalytics,
)
from src.uckn.core.atoms.multi_modal_embeddings_optimized import MultiModalEmbeddingsOptimized

def test_performance_integration(monkeypatch):
    # Dummy ChromaDBConnector
    class DummyChroma:
        def search_documents(self, **kwargs):
            return [{"id": 1, "score": 0.99}]
    cache = CacheManager(max_size=10)
    monitor = ResourceMonitor()
    analytics = PerformanceAnalytics()
    embeddings = MultiModalEmbeddingsOptimized(
        cache_manager=cache,
        resource_monitor=monitor,
        analytics=analytics,
    )
    engine = SemanticSearchEngineOptimized(
        chroma_connector=DummyChroma(),
        embedding_atom=embeddings,
        cache_size=10,
        performance_mode=True,
        enable_async=True,
        enable_batch=True,
        enable_monitoring=True,
        enable_analytics=True,
    )
    # Test search
    result = engine.search({"text": "integration test"}, "code_patterns")
    assert isinstance(result, list)
    # Test batch search
    batch = engine.batch_search([{"text": "a"}, {"code": "b()"}], "code_patterns")
    assert isinstance(batch, list)
    # Test performance summary
    summary = engine.get_performance_summary()
    assert "resource_usage" in summary
    assert "analytics" in summary

def test_performance_mode_toggle():
    engine = SemanticSearchEngineOptimized(chroma_connector=None)
    engine.enable_performance_mode(False)
    assert engine.performance_mode is False
    engine.enable_performance_mode(True)
    assert engine.performance_mode is True
