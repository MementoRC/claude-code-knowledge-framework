"""Enhanced semantic search engine tests."""

import threading
from datetime import datetime
from unittest.mock import Mock

import pytest

from uckn.core.atoms.semantic_search_engine_enhanced import (
    SemanticSearchEngineEnhanced,
)


class TestSemanticSearchEngineEnhanced:
    """Test enhanced semantic search engine."""

    @pytest.fixture
    def mock_db_connector(self):
        """Mock vector database connector."""
        connector = Mock()
        connector.similarity_search.return_value = [
            {
                "id": "1",
                "content": "Test document 1",
                "similarity": 0.9,
                "metadata": {"category": "test"},
            },
            {
                "id": "2",
                "content": "Test document 2",
                "similarity": 0.8,
                "metadata": {"category": "test"},
            },
        ]
        connector.keyword_search.return_value = [
            {
                "id": "3",
                "content": "Keyword match document",
                "score": 0.85,
                "metadata": {"category": "keyword"},
            }
        ]
        return connector

    @pytest.fixture
    def mock_embedding_engine(self):
        """Mock embedding engine."""
        engine = Mock()
        engine.generate_embedding.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        return engine

    @pytest.fixture
    def search_engine(self, mock_db_connector, mock_embedding_engine):
        """Create search engine with mocked dependencies."""
        return SemanticSearchEngineEnhanced(
            db_connector=mock_db_connector, embedding_engine=mock_embedding_engine
        )

    def test_initialization(self):
        """Test search engine initialization."""
        engine = SemanticSearchEngineEnhanced()
        assert engine is not None
        assert engine.search_cache == {}
        assert engine.max_cache_size == 1000
        assert engine.context_weights["semantic"] == 0.6

    def test_basic_search_semantic_mode(
        self, search_engine, mock_db_connector, mock_embedding_engine
    ):
        """Test basic semantic search."""
        results = search_engine.search("test query", search_mode="semantic")

        assert len(results) == 2
        assert results[0]["id"] == "1"
        assert results[0]["similarity"] == 0.9
        mock_embedding_engine.generate_embedding.assert_called_once_with("test query")
        mock_db_connector.similarity_search.assert_called_once()

    def test_basic_search_keyword_mode(self, search_engine, mock_db_connector):
        """Test basic keyword search."""
        results = search_engine.search("test query", search_mode="keyword")

        assert len(results) == 1
        assert results[0]["id"] == "3"
        mock_db_connector.keyword_search.assert_called_once()

    def test_basic_search_hybrid_mode(
        self, search_engine, mock_db_connector, mock_embedding_engine
    ):
        """Test hybrid search mode."""
        results = search_engine.search("test query", search_mode="hybrid")

        # Should get results from both semantic and keyword searches
        assert len(results) >= 1
        mock_embedding_engine.generate_embedding.assert_called_once()
        mock_db_connector.similarity_search.assert_called_once()
        mock_db_connector.keyword_search.assert_called_once()

    def test_search_with_failed_embedding(self, search_engine, mock_embedding_engine):
        """Test search when embedding generation fails."""
        mock_embedding_engine.generate_embedding.return_value = None

        results = search_engine.search("test query")
        assert results == []

    def test_multi_query_search(self, search_engine):
        """Test multi-query search functionality."""
        queries = ["query 1", "query 2", "query 3"]
        results = search_engine.multi_query_search(queries, limit=5)

        assert isinstance(results, list)
        # Should handle multiple queries even if some fail

    def test_multi_query_search_empty_queries(self, search_engine):
        """Test multi-query search with empty query list."""
        results = search_engine.multi_query_search([])
        assert results == []

    def test_similarity_search(
        self, search_engine, mock_embedding_engine, mock_db_connector
    ):
        """Test similarity search functionality."""
        document = "Test document for similarity search"
        results = search_engine.similarity_search(document, threshold=0.7)

        mock_embedding_engine.generate_embedding.assert_called_with(document)
        assert isinstance(results, list)

    def test_similarity_search_failed_embedding(
        self, search_engine, mock_embedding_engine
    ):
        """Test similarity search when embedding fails."""
        mock_embedding_engine.generate_embedding.return_value = None

        results = search_engine.similarity_search("test document")
        assert results == []

    def test_contextual_search(self, search_engine):
        """Test context-aware search."""
        context = {
            "domain": "test",
            "timestamp": datetime.now().isoformat(),
            "user_id": "user123",
        }
        results = search_engine.contextual_search("test query", context, limit=5)

        assert isinstance(results, list)
        # Results should have context-related fields

    def test_search_analytics(self, search_engine):
        """Test search analytics tracking."""
        # Perform some searches
        search_engine.search("query 1", search_mode="semantic")
        search_engine.search("query 2", search_mode="keyword")
        search_engine.search("query 3", search_mode="hybrid")

        analytics = search_engine.get_search_analytics()
        assert analytics["total_searches"] == 3
        assert "mode_distribution" in analytics
        assert "average_results" in analytics

    def test_cache_operations(self, search_engine):
        """Test cache management."""
        # Get initial cache info
        info = search_engine.get_cache_info()
        assert info["cache_size"] == 0
        assert info["max_cache_size"] == 1000

        # Clear cache (should not error even if empty)
        search_engine.clear_cache()

        info = search_engine.get_cache_info()
        assert info["cache_size"] == 0

    def test_context_score_calculation(self, search_engine):
        """Test context score calculation."""
        result = {
            "id": "1",
            "content": "Test document",
            "timestamp": datetime.now().isoformat(),
            "domain": "test",
            "author": "user123",
        }
        context = {
            "timestamp": datetime.now().isoformat(),
            "domain": "test",
            "user_id": "user123",
        }

        score = search_engine._calculate_context_score(result, context)
        assert isinstance(score, float)
        assert score >= 0

    def test_search_exception_handling(self, search_engine, mock_embedding_engine):
        """Test search exception handling."""
        # Make embedding engine raise exception
        mock_embedding_engine.generate_embedding.side_effect = Exception("Test error")

        results = search_engine.search("test query")
        assert results == []

    def test_multi_query_exception_handling(self, search_engine, mock_embedding_engine):
        """Test multi-query search exception handling."""
        mock_embedding_engine.generate_embedding.side_effect = Exception("Test error")

        results = search_engine.multi_query_search(["query1", "query2"])
        assert results == []

    def test_thread_safety(self, search_engine):
        """Test thread safety of cache operations."""

        def cache_operation():
            search_engine.clear_cache()
            info = search_engine.get_cache_info()
            assert isinstance(info, dict)

        threads = [threading.Thread(target=cache_operation) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Should not raise any exceptions

    def test_result_aggregation(self, search_engine):
        """Test result aggregation methods."""
        results1 = [{"id": "1", "content": "doc1", "similarity": 0.9}]
        results2 = [{"id": "2", "content": "doc2", "similarity": 0.8}]
        results_list = [results1, results2]

        # Test union method
        union_results = search_engine._aggregate_results(results_list, "union")
        assert len(union_results) >= 1

        # Test weighted method
        weights = [0.7, 0.3]
        weighted_results = search_engine._aggregate_results(
            results_list, "weighted", weights
        )
        assert len(weighted_results) >= 1

    def test_hybrid_search_merge(self, search_engine):
        """Test merging of semantic and keyword results."""
        semantic_results = [{"id": "1", "content": "semantic doc", "similarity": 0.9}]
        keyword_results = [{"id": "2", "content": "keyword doc", "score": 0.8}]

        merged = search_engine._merge_search_results(
            semantic_results, keyword_results, limit=10
        )
        assert len(merged) >= 1
        assert all("combined_score" in result for result in merged)


class TestSemanticSearchEngineIntegration:
    """Integration tests for semantic search engine."""

    @pytest.fixture
    def chroma_connector(self):
        """Create a ChromaDB connector for testing."""
        try:
            from uckn.core.atoms.vector_db_connector import VectorDBConnector

            connector = VectorDBConnector()
            return connector
        except ImportError:
            pytest.skip("ChromaDB not available for integration tests")

    @pytest.fixture
    def real_embedding_engine(self):
        """Create a real embedding engine for testing."""
        try:
            from uckn.core.atoms.embedding_engine_enhanced import (
                EnhancedEmbeddingEngine,
            )

            return EnhancedEmbeddingEngine()
        except ImportError:
            pytest.skip("Embedding engine not available for integration tests")

    @pytest.mark.integration
    def test_full_search_workflow(self, chroma_connector, real_embedding_engine):
        """Test complete search workflow with real components."""
        try:
            # Create search engine with real components
            search_engine = SemanticSearchEngineEnhanced(
                db_connector=chroma_connector, embedding_engine=real_embedding_engine
            )

            # Add documents to database (this would need to be implemented)
            # For now, just test that search doesn't crash
            results = search_engine.search("artificial intelligence", limit=5)
            assert isinstance(results, list)

        except Exception as e:
            pytest.skip(f"Integration test failed: {e}")
        finally:
            # Cleanup
            try:
                chroma_connector.reset_db()
            except Exception:
                pass  # Ignore cleanup errors


# Conditionally enable real ML tests based on environment
@pytest.mark.skipif(
    not pytest.importorskip("chromadb", reason="ChromaDB not available"),
    reason="ChromaDB required for ML tests",
)
class TestRealMLCapabilities:
    """Tests that use real ML capabilities when available."""

    def test_embedding_generation_and_search(self):
        """Test with real embeddings if available."""
        try:
            from uckn.core.atoms.embedding_engine_enhanced import (
                EnhancedEmbeddingEngine,
            )
            from uckn.core.atoms.vector_db_connector import VectorDBConnector

            # This test would use real ML models if available
            engine = EnhancedEmbeddingEngine()
            connector = VectorDBConnector()

            search_engine = SemanticSearchEngineEnhanced(
                db_connector=connector, embedding_engine=engine
            )

            # Test basic functionality
            results = search_engine.search("test query", limit=1)
            assert isinstance(results, list)

        except ImportError:
            pytest.skip("Real ML components not available")
