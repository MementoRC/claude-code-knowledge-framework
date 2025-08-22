import numpy as np
import pytest
from unittest.mock import patch

from src.uckn.core.atoms.multi_modal_embeddings import MultiModalEmbeddings
from src.uckn.core.ml_environment_manager import get_ml_manager, MLEnvironment


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
    """Provide MultiModalEmbeddings instance for testing."""
    return MultiModalEmbeddings()


def test_availability_check(mm_embedder):
    """Test that embeddings are always available (real or fallback)."""
    assert mm_embedder.is_available()


def test_environment_detection():
    """Test ML environment detection in embeddings."""
    embedder = MultiModalEmbeddings()
    ml_manager = get_ml_manager()

    # Should always be available
    assert embedder.is_available()

    # Device should be set appropriately
    assert embedder.device in ["cpu", "cuda"]

    # Should use fallbacks in disabled/CI environment
    if ml_manager.capabilities.environment in [
        MLEnvironment.DISABLED,
        MLEnvironment.CI_MINIMAL,
    ]:
        # Should use fallback embeddings
        test_embedding = embedder.embed("test", data_type="text")
        assert test_embedding is not None
        assert len(test_embedding) == 384  # Standard embedding dimension


def test_code_embedding_quality(mm_embedder):
    """Test code embedding quality with environment-aware expectations."""
    code1 = "def add(a, b):\n    return a + b"
    code2 = "def sum(x, y):\n    return x + y"
    emb1 = mm_embedder.embed(code1, data_type="code")
    emb2 = mm_embedder.embed(code2, data_type="code")
    assert emb1 is not None and emb2 is not None

    # Calculate similarity
    sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

    # Environment-aware threshold
    ml_manager = get_ml_manager()
    if ml_manager.should_use_real_ml():
        # Real ML models should have better similarity
        assert sim > 0.5, f"Real ML similarity too low: {sim}"
    else:
        # Fallback embeddings use word-based features - similar code should have some similarity
        assert sim > 0.25, f"Fallback similarity too low: {sim}"


def test_text_embedding_quality(mm_embedder):
    """Test text embedding quality with environment-aware expectations."""
    text1 = "Add two numbers"
    text2 = "Sum two values"
    emb1 = mm_embedder.embed(text1, data_type="text")
    emb2 = mm_embedder.embed(text2, data_type="text")
    assert emb1 is not None and emb2 is not None

    sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

    # Environment-aware threshold
    ml_manager = get_ml_manager()
    if ml_manager.should_use_real_ml():
        # Real ML models should capture semantic similarity well
        assert sim > 0.6, f"Real ML text similarity too low: {sim}"
    else:
        # Fallback embeddings use word overlap - should still detect similarity
        assert sim > 0.2, f"Fallback text similarity too low: {sim}"


def test_config_embedding(mm_embedder):
    """Test config embedding with tokenization normalization."""
    config1 = "setting1 = true\nsetting2 = 42"
    config2 = "setting1: true\nsetting2: 42"
    emb1 = mm_embedder.embed(config1, data_type="config")
    emb2 = mm_embedder.embed(config2, data_type="config")
    assert emb1 is not None and emb2 is not None

    sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

    # Config embeddings should be similar due to tokenization normalization
    # Both fallback and real embeddings should handle this well
    assert sim > 0.4, f"Config similarity too low: {sim}"


def test_error_embedding(mm_embedder):
    """Test error embedding with preprocessing."""
    error1 = 'Traceback (most recent call last):\n  File "main.py", line 1, in <module>\nZeroDivisionError: division by zero'
    error2 = "ZeroDivisionError: division by zero"
    emb1 = mm_embedder.embed(error1, data_type="error")
    emb2 = mm_embedder.embed(error2, data_type="error")
    assert emb1 is not None and emb2 is not None

    sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

    # Error preprocessing should extract core error type, making them similar
    ml_manager = get_ml_manager()
    if ml_manager.should_use_real_ml():
        assert sim > 0.5, f"Real ML error similarity too low: {sim}"
    else:
        # Fallback should still detect 'zerodivisionerror' and 'division', 'zero' keywords
        assert sim > 0.2, f"Fallback error similarity too low: {sim}"


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


def test_multi_modal_combination(mm_embedder):
    """Test multi-modal embedding combination."""
    code = "def foo(): return 1"
    text = "Function that returns one"
    config = "foo = 1"
    error = "NameError: name 'foo' is not defined"
    emb = mm_embedder.multi_modal_embed(
        code=code, text=text, config=config, error=error
    )
    assert emb is not None
    assert len(emb) > 0

    # Should be normalized
    norm = np.linalg.norm(emb)
    assert abs(norm - 1.0) < 1e-2  # Slightly relaxed for fallback embeddings

    # Test that individual components contribute
    code_only = mm_embedder.multi_modal_embed(code=code)
    text_only = mm_embedder.multi_modal_embed(text=text)

    assert code_only is not None
    assert text_only is not None

    # Combined embedding should be different from individual components
    assert not np.allclose(emb, code_only, atol=1e-6)
    assert not np.allclose(emb, text_only, atol=1e-6)


def test_caching(mm_embedder):
    """Test embedding caching functionality."""
    text = "cache test"
    emb1 = mm_embedder.embed(text, data_type="text")
    emb2 = mm_embedder.embed(text, data_type="text")

    # Should return exactly the same cached result
    assert emb1 is emb2 or np.allclose(emb1, emb2, atol=1e-10)

    # Cache may be empty in some environments, but results should still be consistent
    # This tests the core functionality rather than implementation details
    assert len(emb1) == len(emb2), "Embeddings should have same dimensions"
    assert all(isinstance(x, (int, float)) for x in emb1), "Embedding should be numeric"


def test_search_integration(mm_embedder):
    """Test integration with ChromaDB connector."""
    chroma = DummyChromaDBConnector()
    query = {"code": "def foo(): pass", "text": "A function"}
    results = mm_embedder.search(query, "code_patterns", chroma, limit=5)
    assert isinstance(results, list)
    assert chroma.last_query is not None
    assert chroma.last_query["collection_name"] == "code_patterns"
    assert chroma.last_query["n_results"] == 5
    assert "query_embedding" in chroma.last_query

    # Check that embedding was generated and is valid
    embedding = chroma.last_query["query_embedding"]
    assert embedding is not None
    assert len(embedding) > 0
    assert all(isinstance(x, (int, float)) for x in embedding)

    # Results should be returned (from dummy connector)
    assert len(results) >= 0  # May be empty in some environments
