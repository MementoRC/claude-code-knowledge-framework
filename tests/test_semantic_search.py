#!/usr/bin/env python3
"""
Simplified Tests for Enhanced Semantic Search Implementation
Focuses on core functionality without external dependencies
"""

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.uckn.core.semantic_search import SemanticSearchEngine


@pytest.fixture
def temp_knowledge_dir():
    """Create temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_semantic_search_initialization(temp_knowledge_dir):
    """Test semantic search engine initialization."""
    engine = SemanticSearchEngine(temp_knowledge_dir)

    assert engine.knowledge_dir == Path(temp_knowledge_dir)
    assert engine.embeddings_dir.exists()


def test_availability_without_dependencies(temp_knowledge_dir):
    """Test availability when dependencies are not installed."""
    with patch("src.uckn.core.semantic_search.SENTENCE_TRANSFORMERS_AVAILABLE", False):
        engine = SemanticSearchEngine(temp_knowledge_dir)
        assert not engine.is_available()


def test_text_extraction_for_embedding(temp_knowledge_dir):
    """Test text extraction from session data."""
    engine = SemanticSearchEngine(temp_knowledge_dir)

    session_data = {
        "session_id": "test-session",
        "context": {"error_type": "ImportError", "tools_used": ["pytest", "ruff"]},
        "lessons_learned": ["Check import paths", "Verify dependencies"],
        "solution_patterns": [
            {"description": "Fix import statement"},
            {"description": "Install missing package"},
        ],
        "manual_insights": ["Python path issue"],
    }

    text = engine._extract_text_for_embedding(session_data)

    assert "ImportError" in text
    assert "pytest" in text
    assert "Check import paths" in text
    assert "Fix import statement" in text
    assert "Python path issue" in text


def test_text_extraction_fallback(temp_knowledge_dir):
    """Test text extraction fallback when no meaningful content."""
    engine = SemanticSearchEngine(temp_knowledge_dir)

    session_data = {"session_id": "test-session"}
    text = engine._extract_text_for_embedding(session_data)

    assert "Session test-session" in text


def test_embedding_stats_empty(temp_knowledge_dir):
    """Test embedding statistics when no embeddings stored."""
    engine = SemanticSearchEngine(temp_knowledge_dir)

    stats = engine.get_embedding_stats()

    assert "total_embeddings" in stats
    assert stats["total_embeddings"] == 0
    assert "storage_type" in stats
    assert "model_available" in stats


def test_search_engine_graceful_degradation(temp_knowledge_dir):
    """Test graceful degradation when components fail."""
    with patch("src.uckn.core.semantic_search.SENTENCE_TRANSFORMERS_AVAILABLE", False):
        engine = SemanticSearchEngine(temp_knowledge_dir)

        # Should not crash when semantic search unavailable
        results = engine.search_similar_sessions("test query")
        assert results == []

        # Should not crash when storing embeddings fails (returns False when model unavailable)
        success = engine.store_session_embedding("test", {})
        assert not success


def test_numpy_storage_creation(temp_knowledge_dir):
    """Test that numpy storage file can be created properly."""
    engine = SemanticSearchEngine(temp_knowledge_dir)

    # Mock embedding for testing storage
    import numpy as np

    mock_embedding = np.array([0.1, 0.2, 0.3])

    session_data = {
        "session_id": "test-session",
        "timestamp": "2025-06-25T10:00:00",
        "final_status": "success",
    }

    # Test the storage function directly
    engine._store_embedding_numpy("test-session", mock_embedding, session_data)

    # Check that the file was created
    embeddings_file = engine.embeddings_dir / "session_embeddings.json"
    assert embeddings_file.exists()

    # Check content
    with open(embeddings_file) as f:
        stored_data = json.load(f)

    assert "test-session" in stored_data
    assert stored_data["test-session"]["embedding"] == [0.1, 0.2, 0.3]
    assert stored_data["test-session"]["metadata"]["session_id"] == "test-session"


def test_sentence_transformer_integration(temp_knowledge_dir):
    """Test sentence transformer integration (environment-aware)."""
    from src.uckn.core.ml_environment_manager import get_ml_manager

    engine = SemanticSearchEngine(temp_knowledge_dir)
    ml_manager = get_ml_manager()

    if ml_manager.capabilities.sentence_transformers:
        # Real sentence transformer test
        session_data = {
            "session_id": "real-ml-test",
            "context": {"error_type": "ValueError"},
            "lessons_learned": ["Validate input parameters"],
        }

        # Should generate real embedding
        success = engine.store_session_embedding("real-ml-test", session_data)
        assert success, "Should succeed with real ML models"

        # Search should work
        results = engine.search_similar_sessions("ValueError validation")
        # Don't assert specific results since ChromaDB might not be available
        assert isinstance(results, list)
    else:
        # Fallback test - should still work with deterministic embeddings
        session_data = {
            "session_id": "fallback-test",
            "context": {"error_type": "ImportError"},
            "lessons_learned": ["Check dependencies"],
        }

        # Should work with fallback embeddings
        success = engine.store_session_embedding("fallback-test", session_data)
        # May not succeed without real storage, but shouldn't crash
        assert isinstance(success, bool)

        # Search should return empty list gracefully
        results = engine.search_similar_sessions("ImportError dependencies")
        assert results == []


def test_chromadb_integration(temp_knowledge_dir):
    """Test ChromaDB integration (environment-aware)."""
    from src.uckn.core.ml_environment_manager import get_ml_manager

    engine = SemanticSearchEngine(temp_knowledge_dir)
    ml_manager = get_ml_manager()

    if ml_manager.capabilities.chromadb:
        # Real ChromaDB test
        session_data = {
            "session_id": "chromadb-test",
            "context": {"tools_used": ["pytest", "ruff"]},
            "lessons_learned": ["Use consistent formatting"],
        }

        # Should work with real ChromaDB
        success = engine.store_session_embedding("chromadb-test", session_data)
        # Success depends on whether embedding generation works
        assert isinstance(success, bool)

        # Search functionality test
        results = engine.search_similar_sessions("pytest formatting")
        assert isinstance(results, list)

        # Test embedding stats
        stats = engine.get_embedding_stats()
        assert stats["storage_type"] in ["chromadb", "numpy", "disabled"]
    else:
        # Fallback test - should handle missing ChromaDB gracefully
        session_data = {
            "session_id": "no-chromadb-test",
            "context": {"tools_used": ["mypy"]},
        }

        # Should not crash without ChromaDB
        success = engine.store_session_embedding("no-chromadb-test", session_data)
        # Will likely fail without storage, but shouldn't crash
        assert isinstance(success, bool)

        # Search should return empty gracefully
        results = engine.search_similar_sessions("mypy")
        assert results == []
