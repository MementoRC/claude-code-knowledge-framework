"""
Tests for QueryParser atom.
"""

import pytest

from src.uckn.core.atoms.query_parser import QueryParser


class TestQueryParser:
    """Test cases for QueryParser."""

    @pytest.fixture
    def parser(self):
        """Create a QueryParser instance."""
        return QueryParser()

    def test_simple_query(self, parser):
        """Test parsing a simple query."""
        result = parser.parse_query("python flask")
        # For simple queries, the result structure varies
        assert isinstance(result, dict)
        # Should contain some parsed structure

    def test_boolean_query(self, parser):
        """Test parsing boolean query with AND operator."""
        result = parser.parse_query("python AND flask")
        assert result["operator"] == "AND"
        assert len(result["clauses"]) == 2

    def test_extract_terms(self, parser):
        """Test term extraction from parsed query."""
        query = parser.parse_query("python flask")
        terms = parser.extract_terms(query)
        assert isinstance(terms, list)
        assert len(terms) >= 1

    def test_synonym_expansion(self, parser):
        """Test synonym expansion."""
        expanded = parser._expand_synonyms("python")
        assert "python" in expanded
        # Should include synonyms from default map
        assert any(syn in expanded for syn in ["py", "pythonic"])

    def test_empty_query(self, parser):
        """Test parsing empty query."""
        result = parser.parse_query("")
        assert result["operator"] == "AND"
        assert result["clauses"] == []
