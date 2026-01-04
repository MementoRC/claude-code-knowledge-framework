import os

import numpy as np
import pytest

from src.uckn.core.atoms.multi_modal_embeddings import MultiModalEmbeddings

# Check if ML dependencies are available
import importlib.util

ML_DEPENDENCIES_AVAILABLE = (
    importlib.util.find_spec("sentence_transformers") is not None
    and importlib.util.find_spec("transformers") is not None
)

# Skip ML model tests in CI environment to avoid network requests and timeouts
SKIP_ML_TESTS = (
    os.getenv("ENVIRONMENT") == "ci"
    or os.getenv("CI") == "true"
    or not ML_DEPENDENCIES_AVAILABLE
)


class DummyChromaDBConnector:
    def __init__(self):
        self.last_query = None

    def search_documents(
        self, collection_name, query_embedding, n_results, min_similarity, where_clause
    ):
        self.last_query = {
            "collection_name": collection_name,
            "query_embedding": query_embedding,
            "n_results": n_results,
            "min_similarity": min_similarity,
            "where_clause": where_clause,
        }
        # Return dummy results
        return [
            {"id": "1", "document": "dummy", "metadata": {}, "similarity_score": 0.99}
        ]


@pytest.fixture(scope="module")
def mm_embedder():
    if SKIP_ML_TESTS:
        pytest.skip("Skipping ML model tests in CI environment")
    return MultiModalEmbeddings()


@pytest.mark.skipif(
    SKIP_ML_TESTS,
    reason="ML dependencies not available or running in CI environment",
)
def test_code_embedding_quality(mm_embedder):
    code1 = "def add(a, b):\n    return a + b"
    code2 = "def sum(x, y):\n    return x + y"
    emb1 = mm_embedder.embed(code1, data_type="code")
    emb2 = mm_embedder.embed(code2, data_type="code")
    assert emb1 is not None and emb2 is not None
    sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    assert sim > 0.8  # Similar code should have high similarity


@pytest.mark.skipif(
    SKIP_ML_TESTS,
    reason="ML dependencies not available or running in CI environment",
)
def test_text_embedding_quality(mm_embedder):
    text1 = "Add two numbers"
    text2 = "Sum two values"
    emb1 = mm_embedder.embed(text1, data_type="text")
    emb2 = mm_embedder.embed(text2, data_type="text")
    assert emb1 is not None and emb2 is not None
    sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    assert sim > 0.6  # Lowered threshold for semantic similarity


@pytest.mark.skipif(
    SKIP_ML_TESTS,
    reason="ML dependencies not available or running in CI environment",
)
def test_config_embedding(mm_embedder):
    config1 = "setting1 = true\nsetting2 = 42"
    config2 = "setting1: true\nsetting2: 42"
    emb1 = mm_embedder.embed(config1, data_type="config")
    emb2 = mm_embedder.embed(config2, data_type="config")
    assert emb1 is not None and emb2 is not None
    sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    assert sim > 0.7


@pytest.mark.skipif(
    SKIP_ML_TESTS,
    reason="ML dependencies not available or running in CI environment",
)
def test_error_embedding(mm_embedder):
    error1 = 'Traceback (most recent call last):\n  File "main.py", line 1, in <module>\nZeroDivisionError: division by zero'
    error2 = "ZeroDivisionError: division by zero"
    emb1 = mm_embedder.embed(error1, data_type="error")
    emb2 = mm_embedder.embed(error2, data_type="error")
    assert emb1 is not None and emb2 is not None
    sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    assert sim > 0.8


@pytest.mark.skipif(
    SKIP_ML_TESTS,
    reason="ML dependencies not available or running in CI environment",
)
def test_batch_processing(mm_embedder):
    items = [
        {"type": "text", "content": "Hello world"},
        {"type": "code", "content": "def foo(): pass"},
        {"type": "config", "content": "foo = bar"},
        {"type": "error", "content": "ValueError: invalid value"},
    ]
    embs = mm_embedder.embed_batch(items)
    assert all(e is not None for e in embs)
    assert len(embs) == 4


@pytest.mark.skipif(
    SKIP_ML_TESTS,
    reason="ML dependencies not available or running in CI environment",
)
def test_multi_modal_combination(mm_embedder):
    code = "def foo(): return 1"
    text = "Function that returns one"
    config = "foo = 1"
    error = "NameError: name 'foo' is not defined"
    emb = mm_embedder.multi_modal_embed(
        code=code, text=text, config=config, error=error
    )
    assert emb is not None
    # Should be normalized
    norm = np.linalg.norm(emb)
    assert abs(norm - 1.0) < 1e-3


def test_caching(mm_embedder):
    text = "cache test"
    emb1 = mm_embedder.embed(text, data_type="text")
    emb2 = mm_embedder.embed(text, data_type="text")
    assert emb1 is emb2 or np.allclose(emb1, emb2)


@pytest.mark.skipif(
    SKIP_ML_TESTS,
    reason="ML dependencies not available or running in CI environment",
)
def test_search_integration(mm_embedder):
    chroma = DummyChromaDBConnector()
    query = {"code": "def foo(): pass", "text": "A function"}
    results = mm_embedder.search(query, "code_patterns", chroma, limit=5)
    assert isinstance(results, list)
    assert chroma.last_query is not None
    assert chroma.last_query["collection_name"] == "code_patterns"
    assert chroma.last_query["n_results"] == 5
    assert "query_embedding" in chroma.last_query
    assert results[0]["similarity_score"] > 0.5
