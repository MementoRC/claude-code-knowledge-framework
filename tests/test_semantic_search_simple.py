#!/usr/bin/env python3
"""
Simplified tests for Enhanced Semantic Search Implementation
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from framework.core.semantic_search import SemanticSearchEngine


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
    

def test_text_extraction_for_embedding(temp_knowledge_dir):
    """Test text extraction from session data."""
    engine = SemanticSearchEngine(temp_knowledge_dir)
    
    session_data = {
        "session_id": "test-session",
        "context": {
            "error_type": "ImportError",
            "tools_used": ["pytest", "ruff"]
        },
        "lessons_learned": ["Check import paths", "Verify dependencies"],
        "solution_patterns": [
            {"description": "Fix import statement"},
            {"description": "Install missing package"}
        ],
        "manual_insights": ["Python path issue"]
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
    engine = SemanticSearchEngine(temp_knowledge_dir)
    
    # Should not crash when semantic search unavailable
    results = engine.search_similar_sessions("test query")
    assert isinstance(results, list)
    
    # Should not crash when storing embeddings fails
    success = engine.store_session_embedding("test", {})
    assert isinstance(success, bool)


def test_availability_check(temp_knowledge_dir):
    """Test availability checking."""
    engine = SemanticSearchEngine(temp_knowledge_dir)
    
    # Should return a boolean
    available = engine.is_available()
    assert isinstance(available, bool)


def test_integration_with_knowledge_manager(temp_knowledge_dir):
    """Test integration with knowledge manager."""
    from framework.core.knowledge_manager import ClaudeCodeKnowledgeManager
    
    km = ClaudeCodeKnowledgeManager(temp_knowledge_dir)
    
    # Should have semantic search engine
    assert hasattr(km, 'semantic_search')
    assert isinstance(km.semantic_search, SemanticSearchEngine)
    
    # Should be able to search (even if returns empty)
    results = km.search_knowledge("test query")
    assert isinstance(results, list)