from src.uckn.core.atoms.semantic_search_engine_optimized import (
    SemanticSearchEngineOptimized,
)


def test_db_search_optimization(monkeypatch):
    calls = []

    class DummyChroma:
        def search_documents(self, **kwargs):
            calls.append(kwargs)
            return [{"id": 1, "score": 0.8}]

    engine = SemanticSearchEngineOptimized(chroma_connector=DummyChroma())
    result = engine.search({"text": "optimize db"}, "code_patterns")
    assert isinstance(result, list)
    assert calls
    # Check that limit and min_similarity are passed
    assert calls[0]["n_results"] == 10
    assert calls[0]["min_similarity"] == 0.7
