import asyncio

import pytest

from src.uckn.core.atoms.semantic_search_engine_optimized import (
    SemanticSearchEngineOptimized,
)


@pytest.mark.asyncio
async def test_async_search(monkeypatch):
    class DummyChroma:
        def search_documents(self, **kwargs):
            return [{"id": 1, "score": 0.99}]
    engine = SemanticSearchEngineOptimized(chroma_connector=DummyChroma())
    # Patch search to count calls
    called = {}
    def fake_search(*a, **k):
        called["yes"] = True
        return [{"id": 2}]
    engine.search = fake_search
    result = await engine._async_search({"text": "foo"}, "code_patterns")
    assert called["yes"]
    assert isinstance(result, list)
