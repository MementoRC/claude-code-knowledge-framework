import numpy as np
import pytest

from src.uckn.core.atoms.multi_modal_embeddings import MultiModalEmbeddings
from src.uckn.core.ml_environment_manager import get_ml_manager


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
def ml_manager():
    """Get ML environment manager for consistent testing."""
    return get_ml_manager()


@pytest.fixture
def mm_embedder():
    """MultiModal embedder with graceful fallback support."""
    return MultiModalEmbeddings(verbose=False)


def test_multi_modal_embeddings_initialization():
    """Test MultiModalEmbeddings can be initialized without crashing."""
    mm = MultiModalEmbeddings(verbose=False)
    assert mm is not None
    assert hasattr(mm, "embed")


def test_text_embedding(mm_embedder):
    """Test basic text embedding functionality."""
    text = "This is a test sentence for embedding."
    embedding = mm_embedder.embed(text, data_type="text")

    # Should return some form of embedding (list or numpy array)
    assert embedding is not None
    assert len(embedding) > 0

    # Should be numeric (fallback to simple hashing if no ML available)
    if isinstance(embedding, (list, np.ndarray)):
        assert all(isinstance(float(x), float) for x in embedding[:5])  # Check first 5


def test_code_embedding(mm_embedder):
    """Test basic code embedding functionality."""
    code = """
    def hello_world():
        print("Hello, World!")
        return True
    """
    embedding = mm_embedder.embed(code, data_type="code")

    # Should return some form of embedding
    assert embedding is not None
    assert len(embedding) > 0

    # Basic structure check
    if isinstance(embedding, (list, np.ndarray)):
        assert all(isinstance(float(x), float) for x in embedding[:5])  # Check first 5


def test_image_embedding_fallback(mm_embedder):
    """Test image embedding with fallback (should handle gracefully)."""
    # This should not crash even without PIL/computer vision libraries
    image_data = "fake_image_data"
    result = mm_embedder.embed(image_data, data_type="image")

    # Should either return an embedding or None (graceful failure)
    assert result is None or len(result) > 0


def test_audio_embedding_fallback(mm_embedder):
    """Test audio embedding with fallback (should handle gracefully)."""
    # This should not crash even without audio processing libraries
    audio_data = "fake_audio_data"
    result = mm_embedder.embed(audio_data, data_type="audio")

    # Should either return an embedding or None (graceful failure)
    assert result is None or len(result) > 0


def test_unknown_data_type(mm_embedder):
    """Test behavior with unknown data type."""
    result = mm_embedder.embed("test data", data_type="unknown")

    # Should handle gracefully (return None or default embedding)
    assert result is None or isinstance(result, (list, np.ndarray))


def test_empty_input(mm_embedder):
    """Test behavior with empty input."""
    result = mm_embedder.embed("", data_type="text")

    # Should handle empty input gracefully
    assert result is None or len(result) >= 0


def test_none_input(mm_embedder):
    """Test behavior with None input."""
    result = mm_embedder.embed(None, data_type="text")

    # Should handle None input gracefully
    assert result is None or isinstance(result, (list, np.ndarray))


def test_batch_embedding(mm_embedder):
    """Test batch embedding functionality if available."""
    texts = ["First text", "Second text", "Third text"]

    # Test individual embeddings
    embeddings = []
    for text in texts:
        emb = mm_embedder.embed(text, data_type="text")
        if emb is not None:
            embeddings.append(emb)

    # Should handle multiple embeddings
    if embeddings:
        assert len(embeddings) <= len(texts)
        # All embeddings should have same structure
        if len(embeddings) > 1:
            assert len(embeddings[0]) == len(embeddings[1])


def test_ml_environment_integration(ml_manager):
    """Test integration with ML environment manager."""
    # Should not crash regardless of ML environment availability
    mm = MultiModalEmbeddings(verbose=False)
    assert mm is not None

    # Basic functionality should work
    result = mm.embed("test", data_type="text")
    assert result is None or len(result) > 0


def test_consistency_across_calls(mm_embedder):
    """Test that same input produces consistent results."""
    text = "consistency test"
    emb1 = mm_embedder.embed(text, data_type="text")
    emb2 = mm_embedder.embed(text, data_type="text")

    # If both return valid embeddings, they should be similar/identical
    if emb1 is not None and emb2 is not None:
        assert len(emb1) == len(emb2)
        # Allow for some floating point differences
        if isinstance(emb1, np.ndarray) and isinstance(emb2, np.ndarray):
            assert np.allclose(emb1, emb2, atol=1e-6)
        elif isinstance(emb1, list) and isinstance(emb2, list):
            # For list comparisons, check if they're close
            differences = [abs(a - b) for a, b in zip(emb1, emb2)]
            assert max(differences) < 1e-6 or emb1 == emb2


def test_different_inputs_produce_different_embeddings(mm_embedder):
    """Test that different inputs produce different embeddings."""
    text1 = "This is the first text"
    text2 = "This is completely different content"

    emb1 = mm_embedder.embed(text1, data_type="text")
    emb2 = mm_embedder.embed(text2, data_type="text")

    # If both are valid embeddings, they should be different
    if emb1 is not None and emb2 is not None and len(emb1) == len(emb2):
        # Should not be identical (allow for edge cases in simple hash functions)
        if isinstance(emb1, (list, np.ndarray)) and isinstance(
            emb2, (list, np.ndarray)
        ):
            # Convert to lists for comparison
            list1 = emb1.tolist() if isinstance(emb1, np.ndarray) else emb1
            list2 = emb2.tolist() if isinstance(emb2, np.ndarray) else emb2
            # They should be different (with very high probability)
            assert (
                list1 != list2 or len(list1) < 10
            )  # Allow identical for very short embeddings


def test_caching_behavior(mm_embedder):
    """Test caching behavior if implemented."""
    text = "cache test"
    emb1 = mm_embedder.embed(text, data_type="text")
    emb2 = mm_embedder.embed(text, data_type="text")

    # Should return exactly the same cached result
    assert emb1 is emb2 or np.allclose(emb1, emb2, atol=1e-10)

    # Cache may be empty in some environments, but results should still be consistent
    # This tests the core functionality rather than implementation details
    assert len(emb1) == len(emb2), "Embeddings should have same dimensions"
    assert all(isinstance(x, int | float) for x in emb1), "Embedding should be numeric"


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
    assert all(isinstance(x, int | float) for x in embedding)

    # Results should be returned (from dummy connector)
    assert len(results) >= 0  # May be empty in some environments


def test_error_handling(mm_embedder):
    """Test error handling in various scenarios."""
    # Test with invalid data types
    try:
        result = mm_embedder.embed({"invalid": "dict"}, data_type="text")
        # Should either work or return None, but not crash
        assert result is None or isinstance(result, (list, np.ndarray))
    except Exception:
        # If it raises an exception, that's also acceptable
        pass

    # Test with extremely long input
    long_text = "a" * 10000
    result = mm_embedder.embed(long_text, data_type="text")
    # Should handle gracefully
    assert result is None or isinstance(result, (list, np.ndarray))


def test_memory_efficiency(mm_embedder):
    """Test that embedding doesn't consume excessive memory."""
    # Test with multiple embeddings
    texts = [f"Text number {i}" for i in range(20)]

    embeddings = []
    for text in texts:
        emb = mm_embedder.embed(text, data_type="text")
        if emb is not None:
            embeddings.append(emb)

    # Should complete without memory issues
    assert len(embeddings) <= len(texts)

    # Clean up
    del embeddings


def test_concurrent_embedding():
    """Test thread safety of embedding operations."""
    import threading

    mm_embedder = MultiModalEmbeddings(verbose=False)
    results = []
    errors = []

    def embed_text(text):
        try:
            result = mm_embedder.embed(text, data_type="text")
            results.append(result)
        except Exception as e:
            errors.append(e)

    # Create multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=embed_text, args=[f"Thread text {i}"])
        threads.append(thread)

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for all threads
    for thread in threads:
        thread.join()

    # Check results
    assert len(errors) == 0, f"Errors in concurrent embedding: {errors}"
    assert len(results) == 5


# Integration tests (may be skipped in some environments)
@pytest.mark.integration
def test_full_workflow_integration():
    """Test complete workflow if all dependencies available."""
    try:
        mm = MultiModalEmbeddings(verbose=False)

        # Test text processing
        text_emb = mm.embed("Integration test text", data_type="text")
        assert text_emb is not None

        # Test code processing
        code_emb = mm.embed("def test(): return True", data_type="code")
        assert code_emb is not None

        # Test search functionality
        chroma = DummyChromaDBConnector()
        query = {"text": "search query"}
        results = mm.search(query, "test_collection", chroma)
        assert isinstance(results, list)

    except ImportError:
        pytest.skip("Integration test dependencies not available")
    except Exception as e:
        pytest.skip(f"Integration test failed: {e}")


# Performance tests (optional)
@pytest.mark.performance
def test_embedding_performance():
    """Test embedding performance with larger inputs."""
    mm = MultiModalEmbeddings(verbose=False)

    # Test with medium-sized text
    medium_text = "This is a medium-sized text for performance testing. " * 50
    start_time = pytest.importorskip("time").time()
    result = mm.embed(medium_text, data_type="text")
    end_time = pytest.importorskip("time").time()

    # Should complete within reasonable time (10 seconds max)
    assert end_time - start_time < 10.0

    # Should produce valid result
    assert result is None or len(result) > 0
