"""
Tests for AdvancedSearchEngine molecule.
"""

import pytest
from unittest.mock import MagicMock
from src.uckn.core.molecules.advanced_search_engine import AdvancedSearchEngine


class TestAdvancedSearchEngine:
    """Test cases for AdvancedSearchEngine."""

    @pytest.fixture
    def search_engine(self):
        """Create an AdvancedSearchEngine instance with mocked components."""
        # Mock the semantic search engine
        mock_semantic = MagicMock()
        mock_semantic.search_by_text.return_value = [
            {
                "id": "pattern-1",
                "similarity_score": 0.95,
                "metadata": {
                    "technology_stack": ["python", "flask"],
                    "complexity": "moderate"
                }
            },
            {
                "id": "pattern-2", 
                "similarity_score": 0.85,
                "metadata": {
                    "technology_stack": ["python", "django"],
                    "complexity": "simple"
                }
            }
        ]
        
        return AdvancedSearchEngine(semantic_engine=mock_semantic)

    def test_basic_search(self, search_engine):
        """Test basic search functionality."""
        result = search_engine.search("python web framework")
        
        assert "results" in result
        assert "total_count" in result
        assert "search_metadata" in result
        assert result["search_metadata"]["query"] == "python web framework"

    def test_search_with_filters(self, search_engine):
        """Test search with faceted filters."""
        filters = {
            "technology_stack": ["python"],
            "complexity": "moderate"
        }
        
        result = search_engine.search("web framework", filters=filters)
        
        assert "results" in result
        assert result["search_metadata"]["filters_applied"] == filters

    def test_autocomplete_suggestions(self, search_engine):
        """Test autocomplete functionality."""
        suggestions = search_engine.get_autocomplete_suggestions("pyth")
        
        assert isinstance(suggestions, list)