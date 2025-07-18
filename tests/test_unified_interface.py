#!/usr/bin/env python3
"""
Tests for Unified Knowledge Management Interface
"""

from unittest.mock import Mock, patch

# TODO: UnifiedKnowledgeManager needs to be implemented in uckn package
# from uckn.core import UnifiedKnowledgeManager
from uckn.core import KnowledgeManager as UnifiedKnowledgeManager


def test_unified_interface_initialization():
    """Test unified interface can be initialized."""
    manager = UnifiedKnowledgeManager()
    assert manager is not None
    assert manager.KNOWN_CAPABILITIES is not None
    assert len(manager.KNOWN_CAPABILITIES) > 0


def test_get_capabilities():
    """Test capability reporting."""
    manager = UnifiedKnowledgeManager()
    capabilities = manager.get_capabilities()

    assert isinstance(capabilities, dict)
    assert "semantic_search" in capabilities
    assert "pattern_extraction" in capabilities
    assert "session_analysis" in capabilities


def test_health_status():
    """Test health status reporting."""
    manager = UnifiedKnowledgeManager()
    health = manager.get_health_status()

    assert isinstance(health, dict)
    assert "knowledge_manager" in health
    assert "capabilities" in health
    assert "active_features" in health
    assert "feature_template" in health


@patch("uckn.core.KnowledgeManager")
def test_capture_session_knowledge_with_feature_flags(mock_km):
    """Test session knowledge capture with feature flag integration."""
    mock_instance = Mock()
    mock_instance.capture_session_knowledge.return_value = "session-123"
    mock_km.return_value = mock_instance

    manager = UnifiedKnowledgeManager()
    session_data = {"test": "data"}

    result = manager.capture_session_knowledge(session_data)
    assert result == "session-123"
    mock_instance.capture_session_knowledge.assert_called_once()


@patch("uckn.core.KnowledgeManager")
def test_search_knowledge_with_capabilities(mock_km):
    """Test knowledge search with capability checking."""
    mock_instance = Mock()
    mock_instance.search_knowledge.return_value = [{"result": "test"}]
    mock_km.return_value = mock_instance

    manager = UnifiedKnowledgeManager()
    results = manager.search_knowledge("test query")

    assert len(results) == 1
    assert results[0]["result"] == "test"
    mock_instance.search_knowledge.assert_called_once()


def test_graceful_degradation():
    """Test graceful degradation when features are disabled."""
    manager = UnifiedKnowledgeManager()

    # Mock disabled capabilities
    with patch.object(manager, "get_capabilities") as mock_caps:
        mock_caps.return_value = dict.fromkeys(manager.KNOWN_CAPABILITIES, False)

        # Should return default results but not crash
        context_summary = manager.get_session_context_summary()
        assert context_summary["total_sessions"] == 0

        # Should return empty solutions
        solutions = manager.suggest_solutions({}, "test error")
        assert solutions == []

        # Should return disabled status
        backup_result = manager.backup_knowledge_base("/tmp/test")
        assert backup_result is False
