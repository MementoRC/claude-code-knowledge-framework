"""Simple tests for PatternManager molecule to improve coverage."""

from unittest.mock import Mock

import pytest

from uckn.core.molecules.pattern_manager import PatternManager


class TestPatternManagerBasic:
    """Basic tests for PatternManager functionality."""

    @pytest.fixture
    def mock_unified_db(self):
        """Create mock UnifiedDatabase."""
        mock_db = Mock()
        mock_db.is_available.return_value = True
        return mock_db

    @pytest.fixture
    def mock_semantic_search(self):
        """Create mock SemanticSearch."""
        mock_search = Mock()
        mock_search.is_available.return_value = True
        return mock_search

    @pytest.fixture
    def pattern_manager(self, mock_unified_db, mock_semantic_search):
        """Create PatternManager instance with mocks."""
        return PatternManager(mock_unified_db, mock_semantic_search)

    def test_initialization(self, mock_unified_db, mock_semantic_search):
        """Test PatternManager initialization."""
        pm = PatternManager(mock_unified_db, mock_semantic_search)
        assert pm.unified_db is mock_unified_db
        assert pm.semantic_search is mock_semantic_search
        assert hasattr(pm, "_logger")

    def test_add_pattern_db_unavailable(
        self, pattern_manager, mock_unified_db, mock_semantic_search
    ):
        """Test add_pattern when database unavailable."""
        mock_unified_db.is_available.return_value = False

        result = pattern_manager.add_pattern(
            {"document": "Test pattern", "metadata": {"type": "test"}}
        )

        assert result is None

    def test_add_pattern_semantic_search_unavailable(
        self, pattern_manager, mock_unified_db, mock_semantic_search
    ):
        """Test add_pattern when semantic search unavailable."""
        mock_semantic_search.is_available.return_value = False

        result = pattern_manager.add_pattern(
            {"document": "Test pattern", "metadata": {"type": "test"}}
        )

        assert result is None

    def test_add_pattern_missing_document(self, pattern_manager):
        """Test add_pattern with missing document."""
        result = pattern_manager.add_pattern({"metadata": {"type": "test"}})

        assert result is None

    def test_add_pattern_empty_document(self, pattern_manager):
        """Test add_pattern with empty document."""
        result = pattern_manager.add_pattern(
            {"document": "", "metadata": {"type": "test"}}
        )

        assert result is None

    def test_add_pattern_success_basic(
        self, pattern_manager, mock_unified_db, mock_semantic_search
    ):
        """Test successful pattern addition."""
        # Mock successful database operations
        mock_unified_db.add_pattern.return_value = True
        mock_semantic_search.encode.return_value = [0.1, 0.2, 0.3]

        pattern_data = {
            "document": "Test pattern content",
            "metadata": {"type": "test", "language": "python"},
        }

        result = pattern_manager.add_pattern(pattern_data)

        assert result is not None
        assert isinstance(result, str)
        mock_unified_db.add_pattern.assert_called_once()

    def test_add_pattern_with_specific_id(
        self, pattern_manager, mock_unified_db, mock_semantic_search
    ):
        """Test pattern addition with specific ID."""
        mock_unified_db.add_pattern.return_value = True
        mock_semantic_search.encode.return_value = [0.1, 0.2, 0.3]

        pattern_id = "custom-pattern-id"
        pattern_data = {
            "pattern_id": pattern_id,
            "document": "Test pattern content",
            "metadata": {"type": "test"},
        }

        result = pattern_manager.add_pattern(pattern_data)

        assert result == pattern_id

    def test_add_pattern_with_project_id(
        self, pattern_manager, mock_unified_db, mock_semantic_search
    ):
        """Test pattern addition with project ID."""
        mock_unified_db.add_pattern.return_value = True
        mock_semantic_search.encode.return_value = [0.1, 0.2, 0.3]

        pattern_data = {
            "document": "Test pattern content",
            "metadata": {"type": "test"},
            "project_id": "test-project-123",
        }

        result = pattern_manager.add_pattern(pattern_data)

        assert result is not None

        # Verify the call included project_id
        call_args = mock_unified_db.add_pattern.call_args
        assert call_args[1]["project_id"] == "test-project-123"

    def test_add_pattern_database_failure(
        self, pattern_manager, mock_unified_db, mock_semantic_search
    ):
        """Test pattern addition when database operation fails."""
        mock_unified_db.add_pattern.return_value = False
        mock_semantic_search.encode.return_value = [0.1, 0.2, 0.3]

        pattern_data = {
            "document": "Test pattern content",
            "metadata": {"type": "test"},
        }

        result = pattern_manager.add_pattern(pattern_data)

        assert result is None

    def test_add_pattern_embedding_failure(
        self, pattern_manager, mock_unified_db, mock_semantic_search
    ):
        """Test pattern addition when embedding generation fails."""
        mock_semantic_search.encode.return_value = None  # Embedding failure

        pattern_data = {
            "document": "Test pattern content",
            "metadata": {"type": "test"},
        }

        result = pattern_manager.add_pattern(pattern_data)

        assert result is None

    def test_get_pattern_success(self, pattern_manager, mock_unified_db):
        """Test successful pattern retrieval."""
        expected_pattern = {
            "id": "pattern-123",
            "document": "Test pattern",
            "metadata": {"type": "test"},
        }
        mock_unified_db.get_pattern.return_value = expected_pattern

        result = pattern_manager.get_pattern("pattern-123")

        assert result == expected_pattern
        mock_unified_db.get_pattern.assert_called_once_with("pattern-123")

    def test_get_pattern_db_unavailable(self, pattern_manager, mock_unified_db):
        """Test pattern retrieval when database unavailable."""
        mock_unified_db.is_available.return_value = False

        result = pattern_manager.get_pattern("pattern-123")

        assert result is None
        mock_unified_db.get_pattern.assert_not_called()

    def test_get_pattern_not_found(self, pattern_manager, mock_unified_db):
        """Test pattern retrieval when pattern not found."""
        mock_unified_db.get_pattern.return_value = None

        result = pattern_manager.get_pattern("non-existent")

        assert result is None

    def test_search_patterns_basic(
        self, pattern_manager, mock_unified_db, mock_semantic_search
    ):
        """Test basic pattern search."""
        mock_semantic_search.encode.return_value = [0.1, 0.2, 0.3]
        mock_unified_db.search_patterns.return_value = [
            {"id": "pattern-1", "similarity": 0.9},
            {"id": "pattern-2", "similarity": 0.8},
        ]

        result = pattern_manager.search_patterns("test query", limit=10)

        assert len(result) == 2
        assert result[0]["id"] == "pattern-1"
        mock_semantic_search.encode.assert_called_once_with("test query")
        mock_unified_db.search_patterns.assert_called_once()

    def test_search_patterns_semantic_unavailable(
        self, pattern_manager, mock_semantic_search
    ):
        """Test pattern search when semantic search unavailable."""
        mock_semantic_search.is_available.return_value = False

        result = pattern_manager.search_patterns("test query")

        assert result == []

    def test_search_patterns_db_unavailable(
        self, pattern_manager, mock_unified_db, mock_semantic_search
    ):
        """Test pattern search when database unavailable."""
        mock_unified_db.is_available.return_value = False
        mock_semantic_search.encode.return_value = [0.1, 0.2, 0.3]

        result = pattern_manager.search_patterns("test query")

        assert result == []

    def test_search_patterns_no_embeddings(self, pattern_manager, mock_semantic_search):
        """Test pattern search when embeddings cannot be generated."""
        mock_semantic_search.encode.return_value = None

        result = pattern_manager.search_patterns("test query")

        assert result == []

    def test_delete_pattern_success(self, pattern_manager, mock_unified_db):
        """Test successful pattern deletion."""
        mock_unified_db.delete_pattern.return_value = True

        result = pattern_manager.delete_pattern("pattern-123")

        assert result is True
        mock_unified_db.delete_pattern.assert_called_once_with("pattern-123")

    def test_delete_pattern_db_unavailable(self, pattern_manager, mock_unified_db):
        """Test pattern deletion when database unavailable."""
        mock_unified_db.is_available.return_value = False

        result = pattern_manager.delete_pattern("pattern-123")

        assert result is False
        mock_unified_db.delete_pattern.assert_not_called()

    def test_delete_pattern_failure(self, pattern_manager, mock_unified_db):
        """Test pattern deletion failure."""
        mock_unified_db.delete_pattern.return_value = False

        result = pattern_manager.delete_pattern("pattern-123")

        assert result is False
