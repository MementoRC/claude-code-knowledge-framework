"""
Comprehensive tests for Task 3: Enhanced Semantic Search Capabilities

Tests the EnhancedSemanticSearchEngine and SemanticSearch atom integration
with focus on performance optimizations, multi-modal support, and robustness.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import numpy as np
import pytest

# Test configuration
TEST_KNOWLEDGE_DIR = ".test_uckn_enhanced_semantic"


class TestEnhancedSemanticSearchEngine:
    """Test suite for EnhancedSemanticSearchEngine"""

    @classmethod
    def setup_class(cls):
        """Setup test environment"""
        if os.path.exists(TEST_KNOWLEDGE_DIR):
            shutil.rmtree(TEST_KNOWLEDGE_DIR)
        os.makedirs(TEST_KNOWLEDGE_DIR, exist_ok=True)

    @classmethod
    def teardown_class(cls):
        """Cleanup test environment"""
        if os.path.exists(TEST_KNOWLEDGE_DIR):
            shutil.rmtree(TEST_KNOWLEDGE_DIR)

    def setup_method(self):
        """Setup for each test method"""
        # Clear any existing cache
        try:
            from uckn.core.enhanced_semantic_search_engine import (
                EnhancedSemanticSearchEngine,
            )

            if hasattr(EnhancedSemanticSearchEngine.encode, "cache_clear"):
                EnhancedSemanticSearchEngine.encode.cache_clear()
        except ImportError:
            pass

    @patch("uckn.core.semantic_search_enhanced.ChromaDBConnector")
    @patch("uckn.core.semantic_search_enhanced.SentenceTransformer")
    def test_engine_initialization_success(self, mock_st, mock_chromadb_connector):
        """Test successful engine initialization"""
        # Mock successful model loading
        mock_model = MagicMock()
        mock_st.return_value = mock_model

        # Mock ChromaDB
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_chromadb_connector.PersistentClient.return_value = mock_client
        mock_client.get_or_create_collection.return_value = mock_collection

        from uckn.core.enhanced_semantic_search_engine import (
            EnhancedSemanticSearchEngine,
        )

        engine = EnhancedSemanticSearchEngine(knowledge_dir=TEST_KNOWLEDGE_DIR)

        assert engine.is_available()
        assert engine.sentence_model is not None
        assert engine.chroma_client is not None
        assert engine.collection is not None
        mock_st.assert_called_once_with("all-MiniLM-L6-v2")

    @patch("uckn.core.semantic_search_enhanced.SENTENCE_TRANSFORMER_AVAILABLE", False)
    @patch("uckn.core.semantic_search_enhanced.CHROMADB_AVAILABLE", False)
    def test_engine_initialization_dependencies_unavailable(self):
        """Test engine initialization when dependencies are unavailable"""
        from uckn.core.enhanced_semantic_search_engine import (
            EnhancedSemanticSearchEngine,
        )

        engine = EnhancedSemanticSearchEngine(knowledge_dir=TEST_KNOWLEDGE_DIR)

        assert not engine.is_available()
        assert engine.sentence_model is None
        assert engine.chroma_client is None
        assert engine.collection is None

    @patch("uckn.core.semantic_search_enhanced.ChromaDBConnector")
    @patch("uckn.core.semantic_search_enhanced.SentenceTransformer")
    def test_encode_functionality(self, mock_st, mock_chromadb_connector):
        """Test text encoding functionality"""
        # Setup mocks
        mock_model = MagicMock()
        mock_embedding = np.array([0.1, 0.2, 0.3] * 128)  # 384-dim embedding
        mock_model.encode.return_value = mock_embedding
        mock_st.return_value = mock_model

        from uckn.core.enhanced_semantic_search_engine import (
            EnhancedSemanticSearchEngine,
        )

        engine = EnhancedSemanticSearchEngine(knowledge_dir=TEST_KNOWLEDGE_DIR)

        # Test normal text encoding
        text = "This is a test sentence for semantic encoding."
        result = engine.encode(text)

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 384
        mock_model.encode.assert_called_once_with(text, convert_to_numpy=True)

    @patch("uckn.core.semantic_search_enhanced.ChromaDBConnector")
    @patch("uckn.core.semantic_search_enhanced.SentenceTransformer")
    def test_encode_caching(self, mock_st, mock_chromadb_connector):
        """Test LRU caching functionality"""
        # Setup mocks
        mock_model = MagicMock()
        mock_embedding = np.array([0.1] * 384)
        mock_model.encode.return_value = mock_embedding
        mock_st.return_value = mock_model

        from uckn.core.enhanced_semantic_search_engine import (
            EnhancedSemanticSearchEngine,
        )

        engine = EnhancedSemanticSearchEngine(knowledge_dir=TEST_KNOWLEDGE_DIR)

        text = "Cached text example"

        # First call
        result1 = engine.encode(text)
        assert mock_model.encode.call_count == 1

        # Second call with same text should use cache
        result2 = engine.encode(text)
        assert mock_model.encode.call_count == 1  # No additional calls
        assert result1 == result2

    @patch("uckn.core.semantic_search_enhanced.ChromaDBConnector")
    @patch("uckn.core.semantic_search_enhanced.SentenceTransformer")
    def test_encode_invalid_inputs(self, mock_st, mock_chromadb_connector):
        """Test encoding with invalid inputs"""
        mock_st.return_value = MagicMock()

        from uckn.core.enhanced_semantic_search_engine import (
            EnhancedSemanticSearchEngine,
        )

        engine = EnhancedSemanticSearchEngine(knowledge_dir=TEST_KNOWLEDGE_DIR)

        # Test invalid input types
        assert engine.encode(None) is None
        assert engine.encode(123) is None
        assert engine.encode([]) is None
        assert engine.encode("") is None

    @patch("uckn.core.semantic_search_enhanced.ChromaDBConnector")
    @patch("uckn.core.semantic_search_enhanced.SentenceTransformer")
    def test_multimodal_content_encoding(self, mock_st, mock_chromadb_connector):
        """Test encoding different content types"""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1] * 384)
        mock_st.return_value = mock_model

        from uckn.core.enhanced_semantic_search_engine import (
            EnhancedSemanticSearchEngine,
        )

        engine = EnhancedSemanticSearchEngine(knowledge_dir=TEST_KNOWLEDGE_DIR)

        # Test different content types
        test_cases = [
            "Regular text content",
            "def hello_world():\n    print('Hello, world!')",  # Code
            "ERROR: Module not found",  # Error message
            "server:\n  host: localhost\n  port: 8080",  # Configuration
        ]

        for content in test_cases:
            result = engine.encode(content)
            assert result is not None
            assert isinstance(result, list)
            assert len(result) == 384

    @patch("uckn.core.semantic_search_enhanced.ChromaDBConnector")
    @patch("uckn.core.semantic_search_enhanced.SentenceTransformer")
    def test_session_embedding_generation(self, mock_st, mock_chromadb_connector):
        """Test session data embedding generation"""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1] * 384)
        mock_st.return_value = mock_model

        from uckn.core.enhanced_semantic_search_engine import (
            EnhancedSemanticSearchEngine,
        )

        engine = EnhancedSemanticSearchEngine(knowledge_dir=TEST_KNOWLEDGE_DIR)

        session_data = {
            "session_id": "test_session_123",
            "context": {
                "error_type": "ImportError",
                "tools_used": ["pytest", "pip"],
                "problem_statement": "Module import failure",
            },
            "lessons_learned": [
                "Check virtual environment",
                "Verify package installation",
            ],
            "solution_patterns": [
                {"description": "Reinstall package in correct environment"}
            ],
            "manual_insights": ["Environment mismatch common cause"],
            "code_snippets": [{"content": "import missing_module"}],
        }

        result = engine.generate_session_embedding(session_data)

        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.shape == (384,)

        # Verify that encode was called with extracted text
        mock_model.encode.assert_called_once()
        called_text = mock_model.encode.call_args[0][0]
        assert "ImportError" in called_text
        assert "pytest" in called_text
        assert "Module import failure" in called_text

    @patch("uckn.core.semantic_search_enhanced.ChromaDBConnector")
    @patch("uckn.core.semantic_search_enhanced.SentenceTransformer")
    def test_text_extraction_comprehensive(self, mock_st, mock_chromadb_connector):
        """Test comprehensive text extraction from session data"""
        mock_st.return_value = MagicMock()

        from uckn.core.enhanced_semantic_search_engine import (
            EnhancedSemanticSearchEngine,
        )

        engine = EnhancedSemanticSearchEngine(knowledge_dir=TEST_KNOWLEDGE_DIR)

        # Test with comprehensive session data
        session_data = {
            "context": {
                "error_type": "ValueError",
                "tools_used": ["pandas", "numpy"],
                "problem_statement": "Data conversion issue",
            },
            "lessons_learned": ["Type checking important", "Validate input data"],
            "solution_patterns": [
                {"description": "Add proper type conversion"},
                "Use pandas.to_numeric with errors='coerce'",
            ],
            "manual_insights": ["Common data cleaning issue"],
            "code_snippets": [
                {
                    "content": "df['column'] = pd.to_numeric(df['column'], errors='coerce')"
                },
                "import pandas as pd",
            ],
        }

        extracted_text = engine._extract_text_for_embedding(session_data)

        # Verify all components are included
        assert "ValueError" in extracted_text
        assert "pandas" in extracted_text
        assert "Data conversion issue" in extracted_text
        assert "Type checking important" in extracted_text
        assert "Add proper type conversion" in extracted_text
        assert "to_numeric" in extracted_text
        assert "Common data cleaning issue" in extracted_text
        assert "pd.to_numeric" in extracted_text

    @patch("uckn.core.semantic_search_enhanced.ChromaDBConnector")
    @patch("uckn.core.semantic_search_enhanced.SentenceTransformer")
    def test_get_embedding_stats(self, mock_st, mock_chromadb_connector):
        """Test embedding statistics functionality"""
        # Setup mocks
        mock_collection = MagicMock()
        mock_collection.count.return_value = 5
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb_connector.PersistentClient.return_value = mock_client
        mock_st.return_value = MagicMock()

        from uckn.core.enhanced_semantic_search_engine import (
            EnhancedSemanticSearchEngine,
        )

        engine = EnhancedSemanticSearchEngine(knowledge_dir=TEST_KNOWLEDGE_DIR)

        stats = engine.get_embedding_stats()

        assert isinstance(stats, dict)
        assert "total_embeddings" in stats
        assert "storage_type" in stats
        assert "model_available" in stats
        assert stats["total_embeddings"] == 5
        assert stats["storage_type"] == "chromadb"
        assert stats["model_available"] is True

    def test_get_embedding_stats_numpy_fallback(self):
        """Test embedding statistics with numpy fallback"""
        # Create test embeddings file
        test_embeddings = {
            "session1": {"embedding": [0.1] * 384, "metadata": {}},
            "session2": {"embedding": [0.2] * 384, "metadata": {}},
        }

        embeddings_dir = Path(TEST_KNOWLEDGE_DIR) / "embeddings"
        embeddings_dir.mkdir(parents=True, exist_ok=True)
        embeddings_file = embeddings_dir / "session_embeddings.json"

        with open(embeddings_file, "w") as f:
            json.dump(test_embeddings, f)

        with patch(
            "uckn.core.enhanced_semantic_search_engine.SENTENCE_TRANSFORMERS_AVAILABLE",
            False,
        ), patch("uckn.core.enhanced_semantic_search_engine.CHROMADB_AVAILABLE", False):
            from uckn.core.enhanced_semantic_search_engine import (
                EnhancedSemanticSearchEngine,
            )

            engine = EnhancedSemanticSearchEngine(knowledge_dir=TEST_KNOWLEDGE_DIR)

            stats = engine.get_embedding_stats()

            assert stats["total_embeddings"] == 2
            assert stats["storage_type"] == "numpy_fallback"
            assert stats["model_available"] is False


class TestSemanticSearchAtomIntegration:
    """Test suite for SemanticSearch atom integration with enhanced engine"""

    @classmethod
    def setup_class(cls):
        """Setup test environment"""
        if os.path.exists(TEST_KNOWLEDGE_DIR):
            shutil.rmtree(TEST_KNOWLEDGE_DIR)
        os.makedirs(TEST_KNOWLEDGE_DIR, exist_ok=True)

    @classmethod
    def teardown_class(cls):
        """Cleanup test environment"""
        if os.path.exists(TEST_KNOWLEDGE_DIR):
            shutil.rmtree(TEST_KNOWLEDGE_DIR)

    @patch("uckn.core.semantic_search_enhanced.ChromaDBConnector")
    @patch("uckn.core.semantic_search_enhanced.SentenceTransformer")
    def test_semantic_search_atom_initialization(
        self, mock_st, mock_chromadb_connector
    ):
        """Test SemanticSearch atom initialization with enhanced engine"""
        mock_st.return_value = MagicMock()

        from uckn.core.atoms.semantic_search import SemanticSearch

        atom = SemanticSearch(knowledge_dir=TEST_KNOWLEDGE_DIR)

        assert atom.is_available()
        assert atom.engine is not None

    @patch("uckn.core.atoms.semantic_search.SEMANTIC_SEARCH_ENGINE_AVAILABLE", False)
    def test_semantic_search_atom_engine_unavailable(self):
        """Test SemanticSearch atom when engine is unavailable"""
        from uckn.core.atoms.semantic_search import SemanticSearch

        atom = SemanticSearch(knowledge_dir=TEST_KNOWLEDGE_DIR)

        assert not atom.is_available()
        assert atom.engine is None
        assert atom.encode("test") is None

    @patch("uckn.core.semantic_search_enhanced.ChromaDBConnector")
    @patch("uckn.core.semantic_search_enhanced.SentenceTransformer")
    def test_semantic_search_atom_encode_delegation(
        self, mock_st, mock_chromadb_connector
    ):
        """Test that SemanticSearch atom properly delegates to enhanced engine"""
        mock_model = MagicMock()
        mock_embedding = np.array([0.1] * 384)
        mock_model.encode.return_value = mock_embedding
        mock_st.return_value = mock_model

        from uckn.core.atoms.semantic_search import SemanticSearch

        atom = SemanticSearch(knowledge_dir=TEST_KNOWLEDGE_DIR)

        test_text = "Test delegation to enhanced engine"
        result = atom.encode(test_text)

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 384

        # Verify the underlying model was called
        mock_model.encode.assert_called_once_with(test_text, convert_to_numpy=True)


class TestPerformanceOptimizations:
    """Test suite for performance optimization features"""

    @patch("uckn.core.semantic_search_enhanced.ChromaDBConnector")
    @patch("uckn.core.semantic_search_enhanced.SentenceTransformer")
    def test_caching_performance(self, mock_st, mock_chromadb_connector):
        """Test that caching improves performance"""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1] * 384)
        mock_st.return_value = mock_model

        from uckn.core.enhanced_semantic_search_engine import (
            EnhancedSemanticSearchEngine,
        )

        engine = EnhancedSemanticSearchEngine(knowledge_dir=TEST_KNOWLEDGE_DIR)

        # Test multiple calls with same text
        text = "Performance test text"

        # First call
        result1 = engine.encode(text)
        call_count_after_first = mock_model.encode.call_count

        # Multiple subsequent calls
        for _ in range(5):
            result = engine.encode(text)
            assert result == result1  # Same result

        # Model should only be called once due to caching
        assert mock_model.encode.call_count == call_count_after_first

    @patch("uckn.core.semantic_search_enhanced.ChromaDBConnector")
    @patch("uckn.core.semantic_search_enhanced.SentenceTransformer")
    def test_different_inputs_not_cached_together(
        self, mock_st, mock_chromadb_connector
    ):
        """Test that different inputs get different cache entries"""
        mock_model = MagicMock()

        # Return different embeddings for different inputs
        def side_effect(text, convert_to_numpy=True):
            return np.array([hash(text) % 1000 / 1000.0] * 384)

        mock_model.encode.side_effect = side_effect
        mock_st.return_value = mock_model

        from uckn.core.enhanced_semantic_search_engine import (
            EnhancedSemanticSearchEngine,
        )

        engine = EnhancedSemanticSearchEngine(knowledge_dir=TEST_KNOWLEDGE_DIR)

        text1 = "First unique text"
        text2 = "Second unique text"

        result1 = engine.encode(text1)
        result2 = engine.encode(text2)

        # Should be different results
        assert result1 != result2

        # Should have called model twice
        assert mock_model.encode.call_count == 2

        # Calling again should use cache
        result1_cached = engine.encode(text1)
        result2_cached = engine.encode(text2)

        assert result1 == result1_cached
        assert result2 == result2_cached
        # Still only 2 calls to model
        assert mock_model.encode.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
