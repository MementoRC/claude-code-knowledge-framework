#!/usr/bin/env python3
"""
Tests for Unified Knowledge Management Interface
"""

from unittest.mock import Mock, patch

from src.uckn.bridge.unified_interface import UnifiedKnowledgeManager


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


def test_add_knowledge_pattern_with_feature_flags():
    """Test knowledge pattern addition with feature flag integration."""
    with patch("src.uckn.bridge.unified_interface.KnowledgeManager") as mock_km:
        mock_instance = Mock()
        mock_instance.add_pattern.return_value = "pattern-123"
        mock_km.return_value = mock_instance

        manager = UnifiedKnowledgeManager()
        pattern_data = {"document": "test pattern", "metadata": {}}

        result = manager.add_knowledge_pattern(pattern_data)
        assert result == "pattern-123"
        mock_instance.add_pattern.assert_called_once()


def test_search_patterns_with_capabilities():
    """Test pattern search with capability checking."""
    with patch("src.uckn.bridge.unified_interface.KnowledgeManager") as mock_km:
        mock_instance = Mock()
        mock_instance.search_patterns.return_value = [{"result": "test"}]
        mock_km.return_value = mock_instance

        manager = UnifiedKnowledgeManager()
        results = manager.search_patterns("test query")

        assert len(results) == 1
        assert results[0]["result"] == "test"
        mock_instance.search_patterns.assert_called_once()


def test_graceful_degradation():
    """Test graceful degradation when features are disabled."""
    manager = UnifiedKnowledgeManager()

    # Mock disabled capabilities
    with patch.object(manager, "get_capabilities") as mock_caps:
        mock_caps.return_value = {cap: False for cap in manager.KNOWN_CAPABILITIES}

        # Should return None when pattern extraction disabled
        pattern = manager.get_pattern("test-pattern")
        assert pattern is None

        # Should return empty error solutions
        solutions = manager.search_error_solutions("test error")
        assert solutions == []

        # Should return disabled status
        backup_result = manager.backup_knowledge_base("/tmp/test")
        assert backup_result is False
