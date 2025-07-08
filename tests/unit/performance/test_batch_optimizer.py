import pytest

from src.uckn.core.atoms.semantic_search_engine_optimized import (
    SemanticSearchEngineOptimized,
)


def test_batch_search(monkeypatch):
    class DummyChroma:
        def search_documents(self, **kwargs):
            return [{"id": 1, "score": 0.9}]

    engine = SemanticSearchEngineOptimized(chroma_connector=DummyChroma())
    queries = [{"text": "foo"}, {"code": "bar()"}]
    results = engine.batch_search(queries, "code_patterns")
    assert isinstance(results, list)
    assert all(isinstance(r, list) for r in results)
    assert len(results) == 2
