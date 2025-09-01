"""Tests for PatternClassification molecule."""

from unittest.mock import Mock, patch

import pytest

from uckn.core.molecules.pattern_classification import PatternClassification


class TestPatternClassification:
    """Test PatternClassification functionality."""

    @pytest.fixture
    def mock_unified_db(self):
        """Create mock UnifiedDatabase."""
        mock_db = Mock()
        mock_db.is_available.return_value = True
        return mock_db

    @pytest.fixture
    def pattern_classification(self, mock_unified_db):
        """Create PatternClassification instance with mock database."""
        return PatternClassification(mock_unified_db)

    def test_initialization(self, mock_unified_db):
        """Test PatternClassification initialization."""
        pc = PatternClassification(mock_unified_db)
        assert pc.unified_db is mock_unified_db
        assert hasattr(pc, "_logger")

    def test_add_category_success(self, pattern_classification, mock_unified_db):
        """Test successful category addition."""
        mock_unified_db.add_category.return_value = True

        result = pattern_classification.add_category("Test Category", "Description")

        assert result is not None
        assert isinstance(result, str)
        mock_unified_db.add_category.assert_called_once()

        # Verify the call arguments
        call_args = mock_unified_db.add_category.call_args
        assert call_args[1]["name"] == "Test Category"
        assert call_args[1]["description"] == "Description"
        assert "category_id" in call_args[1]

    def test_add_category_with_specific_id(
        self, pattern_classification, mock_unified_db
    ):
        """Test category addition with specific ID."""
        mock_unified_db.add_category.return_value = True
        category_id = "custom-id-123"

        result = pattern_classification.add_category(
            "Test Category", "Description", category_id
        )

        assert result == category_id
        call_args = mock_unified_db.add_category.call_args
        assert call_args[1]["category_id"] == category_id

    def test_add_category_failure(self, pattern_classification, mock_unified_db):
        """Test category addition failure."""
        mock_unified_db.add_category.return_value = False

        result = pattern_classification.add_category("Test Category")

        assert result is None

    def test_add_category_db_unavailable(self, pattern_classification, mock_unified_db):
        """Test category addition when database unavailable."""
        mock_unified_db.is_available.return_value = False

        result = pattern_classification.add_category("Test Category")

        assert result is None
        mock_unified_db.add_category.assert_not_called()

    def test_get_category_success(self, pattern_classification, mock_unified_db):
        """Test successful category retrieval."""
        expected_category = {
            "id": "test-id",
            "name": "Test Category",
            "description": "Test Description",
        }
        mock_unified_db.get_category.return_value = expected_category

        result = pattern_classification.get_category("test-id")

        assert result == expected_category
        mock_unified_db.get_category.assert_called_once_with("test-id")

    def test_get_category_not_found(self, pattern_classification, mock_unified_db):
        """Test category retrieval when not found."""
        mock_unified_db.get_category.return_value = None

        result = pattern_classification.get_category("non-existent")

        assert result is None

    def test_get_category_db_unavailable(self, pattern_classification, mock_unified_db):
        """Test category retrieval when database unavailable."""
        mock_unified_db.is_available.return_value = False

        result = pattern_classification.get_category("test-id")

        assert result is None
        mock_unified_db.get_category.assert_not_called()

    def test_update_category_success(self, pattern_classification, mock_unified_db):
        """Test successful category update."""
        mock_unified_db.update_category.return_value = True

        result = pattern_classification.update_category(
            "test-id", name="New Name", description="New Description"
        )

        assert result is True
        mock_unified_db.update_category.assert_called_once_with(
            "test-id", {"name": "New Name", "description": "New Description"}
        )

    def test_update_category_name_only(self, pattern_classification, mock_unified_db):
        """Test category update with name only."""
        mock_unified_db.update_category.return_value = True

        result = pattern_classification.update_category("test-id", name="New Name")

        assert result is True
        mock_unified_db.update_category.assert_called_once_with(
            "test-id", {"name": "New Name"}
        )

    def test_update_category_description_only(
        self, pattern_classification, mock_unified_db
    ):
        """Test category update with description only."""
        mock_unified_db.update_category.return_value = True

        result = pattern_classification.update_category(
            "test-id", description="New Description"
        )

        assert result is True
        mock_unified_db.update_category.assert_called_once_with(
            "test-id", {"description": "New Description"}
        )

    def test_update_category_no_changes(self, pattern_classification, mock_unified_db):
        """Test category update with no changes."""
        result = pattern_classification.update_category("test-id")

        assert result is False
        mock_unified_db.update_category.assert_not_called()

    def test_update_category_db_unavailable(
        self, pattern_classification, mock_unified_db
    ):
        """Test category update when database unavailable."""
        mock_unified_db.is_available.return_value = False

        result = pattern_classification.update_category("test-id", name="New Name")

        assert result is False
        mock_unified_db.update_category.assert_not_called()

    def test_delete_category_success(self, pattern_classification, mock_unified_db):
        """Test successful category deletion."""
        mock_unified_db.delete_category.return_value = True

        result = pattern_classification.delete_category("test-id")

        assert result is True
        mock_unified_db.delete_category.assert_called_once_with("test-id")

    def test_delete_category_failure(self, pattern_classification, mock_unified_db):
        """Test category deletion failure."""
        mock_unified_db.delete_category.return_value = False

        result = pattern_classification.delete_category("test-id")

        assert result is False

    def test_delete_category_db_unavailable(
        self, pattern_classification, mock_unified_db
    ):
        """Test category deletion when database unavailable."""
        mock_unified_db.is_available.return_value = False

        result = pattern_classification.delete_category("test-id")

        assert result is False
        mock_unified_db.delete_category.assert_not_called()

    def test_assign_pattern_to_category_success(
        self, pattern_classification, mock_unified_db
    ):
        """Test successful pattern assignment to category."""
        # Mock pattern and category existence
        mock_unified_db.get_pattern.return_value = {"id": "pattern-1"}
        mock_unified_db.get_category.return_value = {"id": "category-1"}
        mock_unified_db.assign_pattern_to_category.return_value = True

        result = pattern_classification.assign_pattern_to_category(
            "pattern-1", "category-1"
        )

        assert result is True
        mock_unified_db.assign_pattern_to_category.assert_called_once_with(
            "pattern-1", "category-1"
        )

    def test_assign_pattern_to_category_pattern_not_found(
        self, pattern_classification, mock_unified_db
    ):
        """Test pattern assignment when pattern not found."""
        mock_unified_db.get_pattern.return_value = None  # Pattern not found
        mock_unified_db.get_category.return_value = {"id": "category-1"}

        result = pattern_classification.assign_pattern_to_category(
            "non-existent", "category-1"
        )

        assert result is False
        mock_unified_db.assign_pattern_to_category.assert_not_called()

    def test_assign_pattern_to_category_category_not_found(
        self, pattern_classification, mock_unified_db
    ):
        """Test pattern assignment when category not found."""
        mock_unified_db.get_pattern.return_value = {"id": "pattern-1"}
        mock_unified_db.get_category.return_value = None  # Category not found

        result = pattern_classification.assign_pattern_to_category(
            "pattern-1", "non-existent"
        )

        assert result is False
        mock_unified_db.assign_pattern_to_category.assert_not_called()

    def test_assign_pattern_to_category_db_unavailable(
        self, pattern_classification, mock_unified_db
    ):
        """Test pattern assignment when database unavailable."""
        mock_unified_db.is_available.return_value = False

        result = pattern_classification.assign_pattern_to_category(
            "pattern-1", "category-1"
        )

        assert result is False
        mock_unified_db.assign_pattern_to_category.assert_not_called()

    def test_remove_pattern_from_category_success(
        self, pattern_classification, mock_unified_db
    ):
        """Test successful pattern removal from category."""
        mock_unified_db.remove_pattern_from_category.return_value = True

        result = pattern_classification.remove_pattern_from_category(
            "pattern-1", "category-1"
        )

        assert result is True
        mock_unified_db.remove_pattern_from_category.assert_called_once_with(
            "pattern-1", "category-1"
        )

    def test_remove_pattern_from_category_failure(
        self, pattern_classification, mock_unified_db
    ):
        """Test pattern removal failure."""
        mock_unified_db.remove_pattern_from_category.return_value = False

        result = pattern_classification.remove_pattern_from_category(
            "pattern-1", "category-1"
        )

        assert result is False

    def test_remove_pattern_from_category_db_unavailable(
        self, pattern_classification, mock_unified_db
    ):
        """Test pattern removal when database unavailable."""
        mock_unified_db.is_available.return_value = False

        result = pattern_classification.remove_pattern_from_category(
            "pattern-1", "category-1"
        )

        assert result is False
        mock_unified_db.remove_pattern_from_category.assert_not_called()

    def test_get_patterns_in_category_success(
        self, pattern_classification, mock_unified_db
    ):
        """Test successful retrieval of patterns in category."""
        expected_patterns = ["pattern-1", "pattern-2", "pattern-3"]
        mock_unified_db.get_patterns_by_category.return_value = expected_patterns

        result = pattern_classification.get_patterns_in_category("category-1")

        assert result == expected_patterns
        mock_unified_db.get_patterns_by_category.assert_called_once_with("category-1")

    def test_get_patterns_in_category_empty(
        self, pattern_classification, mock_unified_db
    ):
        """Test retrieval of patterns in empty category."""
        mock_unified_db.get_patterns_by_category.return_value = []

        result = pattern_classification.get_patterns_in_category("category-1")

        assert result == []

    def test_get_patterns_in_category_db_unavailable(
        self, pattern_classification, mock_unified_db
    ):
        """Test pattern retrieval when database unavailable."""
        mock_unified_db.is_available.return_value = False

        result = pattern_classification.get_patterns_in_category("category-1")

        assert result == []
        mock_unified_db.get_patterns_by_category.assert_not_called()

    def test_get_categories_for_pattern_success(
        self, pattern_classification, mock_unified_db
    ):
        """Test successful retrieval of categories for pattern."""
        expected_categories = [
            {"id": "cat-1", "name": "Category 1"},
            {"id": "cat-2", "name": "Category 2"},
        ]
        mock_unified_db.get_pattern_categories.return_value = expected_categories

        result = pattern_classification.get_categories_for_pattern("pattern-1")

        assert result == expected_categories
        mock_unified_db.get_pattern_categories.assert_called_once_with("pattern-1")

    def test_get_categories_for_pattern_empty(
        self, pattern_classification, mock_unified_db
    ):
        """Test retrieval of categories for pattern with no categories."""
        mock_unified_db.get_pattern_categories.return_value = []

        result = pattern_classification.get_categories_for_pattern("pattern-1")

        assert result == []

    def test_get_categories_for_pattern_db_unavailable(
        self, pattern_classification, mock_unified_db
    ):
        """Test category retrieval for pattern when database unavailable."""
        mock_unified_db.is_available.return_value = False

        result = pattern_classification.get_categories_for_pattern("pattern-1")

        assert result == []
        mock_unified_db.get_pattern_categories.assert_not_called()

    def test_logging_behavior(self, pattern_classification, mock_unified_db):
        """Test that appropriate logging occurs."""
        # Test logging when DB is unavailable
        mock_unified_db.is_available.return_value = False

        with patch.object(pattern_classification._logger, "error") as mock_error_log:
            pattern_classification.add_category("Test")
            mock_error_log.assert_called_once()

        with patch.object(
            pattern_classification._logger, "warning"
        ) as mock_warning_log:
            pattern_classification.get_category("test")
            mock_warning_log.assert_called_once()

    def test_uuid_generation(self, pattern_classification, mock_unified_db):
        """Test that UUID is generated when no category_id provided."""
        mock_unified_db.add_category.return_value = True

        with patch(
            "uckn.core.molecules.pattern_classification.uuid.uuid4"
        ) as mock_uuid:
            mock_uuid.return_value = Mock()
            mock_uuid.return_value.__str__ = Mock(return_value="generated-uuid")

            result = pattern_classification.add_category("Test Category")

            assert result == "generated-uuid"
            mock_uuid.assert_called_once()

    def test_edge_cases(self, pattern_classification, mock_unified_db):
        """Test edge cases and boundary conditions."""
        # Test empty strings
        result = pattern_classification.add_category("")
        assert result is not None  # Empty name should still generate UUID

        # Test None values in update
        result = pattern_classification.update_category("test", None, None)
        assert result is False

        # Test successful assignment but DB operation fails
        mock_unified_db.get_pattern.return_value = {"id": "pattern-1"}
        mock_unified_db.get_category.return_value = {"id": "category-1"}
        mock_unified_db.assign_pattern_to_category.return_value = False

        result = pattern_classification.assign_pattern_to_category(
            "pattern-1", "category-1"
        )
        assert result is False
