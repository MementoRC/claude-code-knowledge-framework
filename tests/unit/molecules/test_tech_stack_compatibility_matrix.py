"""
Test TechStackCompatibilityMatrix functionality
"""

import hashlib
import json
from unittest.mock import Mock

import pytest

from src.uckn.core.molecules.tech_stack_compatibility_matrix import (
    TechStackCompatibilityMatrix,
)


class TestTechStackCompatibilityMatrix:
    """Test TechStackCompatibilityMatrix functionality"""

    def setup_method(self):
        """Setup test fixtures for each test method."""
        self.mock_chroma = Mock()
        # Ensure is_available returns True by default for most tests
        self.mock_chroma.is_available.return_value = True
        # Mock collections attribute
        self.mock_chroma.collections = {"tech_stack_compatibility": Mock()}

        # Initialize the TechStackCompatibilityMatrix with the mocked ChromaDB connector
        self.matrix = TechStackCompatibilityMatrix(self.mock_chroma)

    def _generate_expected_combo_id(self, ts_a: list, ts_b: list) -> str:
        """
        Helper to generate the expected ID for a tech stack combo.
        This mimics the internal ID generation logic.
        """
        sorted_ts_a = sorted(ts_a)
        sorted_ts_b = sorted(ts_b)
        combined_sorted_techs = sorted(sorted_ts_a + sorted_ts_b)
        combo_string = json.dumps(combined_sorted_techs)
        return hashlib.sha256(combo_string.encode('utf-8')).hexdigest()

    def test_initialization(self):
        """Test TechStackCompatibilityMatrix initializes correctly."""
        assert self.matrix.chroma_connector == self.mock_chroma
        assert self.matrix._COLLECTION_NAME == "tech_stack_compatibility"

    def test_is_available(self):
        """Test is_available method."""
        assert self.matrix.is_available() is True

        self.mock_chroma.is_available.return_value = False
        assert self.matrix.is_available() is False

    def test_add_tech_stack_combo_success(self):
        """Test adding a new tech stack combination successfully."""
        ts_a = ["Python"]
        ts_b = ["Django"]
        score = 0.8
        description = "Good compatibility for web development."

        expected_id = self._generate_expected_combo_id(ts_a, ts_b)
        # Mock add_document to return True
        self.mock_chroma.add_document.return_value = True

        combo_id = self.matrix.add_tech_stack_combo(ts_a, ts_b, score, description)

        assert combo_id == expected_id
        self.mock_chroma.add_document.assert_called_once()

    def test_add_tech_stack_combo_unavailable(self):
        """Test adding combo when ChromaDB is unavailable."""
        self.mock_chroma.is_available.return_value = False

        combo_id = self.matrix.add_tech_stack_combo(["Python"], ["Django"], 0.8)

        assert combo_id is None
        self.mock_chroma.add_document.assert_not_called()

    def test_add_tech_stack_combo_invalid_score(self):
        """Test adding combo with invalid score."""
        combo_id = self.matrix.add_tech_stack_combo(["Python"], ["Django"], 1.5)  # Invalid score

        assert combo_id is None
        self.mock_chroma.add_document.assert_not_called()

    def test_get_compatibility_score_found(self):
        """Test retrieving an existing compatibility score."""
        ts_a = ["Python"]
        ts_b = ["React"]
        expected_score = 0.65

        # Mock the return value for get_document to simulate finding a document
        self.mock_chroma.get_document.return_value = {
            "metadata": {
                "tech_stack_a": ts_a,
                "tech_stack_b": ts_b,
                "score": expected_score,
                "description": "Moderate compatibility"
            }
        }

        score = self.matrix.get_compatibility_score(ts_a, ts_b)

        assert score == expected_score
        self.mock_chroma.get_document.assert_called_once()

    def test_get_compatibility_score_not_found(self):
        """Test retrieving score for a non-existent combo."""
        self.mock_chroma.get_document.return_value = None  # Simulate document not found

        score = self.matrix.get_compatibility_score(["Java"], ["Spring"])

        assert score is None
        self.mock_chroma.get_document.assert_called_once()

    def test_get_compatibility_score_unavailable(self):
        """Test retrieving score when ChromaDB is unavailable."""
        self.mock_chroma.is_available.return_value = False

        score = self.matrix.get_compatibility_score(["Node.js"], ["MongoDB"])

        assert score is None
        self.mock_chroma.get_document.assert_not_called()

    def test_update_compatibility_score_existing(self):
        """Test updating an existing compatibility score."""
        ts_a = ["Python"]
        ts_b = ["Flask"]
        new_score = 0.95
        new_description = "Excellent compatibility after optimizations."

        # Mock get_document to simulate finding the existing document
        self.mock_chroma.get_document.return_value = {
            "metadata": {
                "tech_stack_a": ts_a,
                "tech_stack_b": ts_b,
                "score": 0.9,
                "description": "Very good"
            }
        }
        # Mock update_document to indicate success
        self.mock_chroma.update_document.return_value = True

        success = self.matrix.update_compatibility_score(ts_a, ts_b, new_score, new_description)

        assert success is True
        self.mock_chroma.get_document.assert_called_once()
        self.mock_chroma.update_document.assert_called_once()

    def test_update_compatibility_score_non_existent(self):
        """Test updating a non-existent compatibility score."""
        ts_a = ["Ruby"]
        ts_b = ["Rails"]
        new_score = 0.75

        # Mock get_document to simulate not finding the document
        self.mock_chroma.get_document.return_value = None

        success = self.matrix.update_compatibility_score(ts_a, ts_b, new_score, "Good")

        assert success is False
        self.mock_chroma.get_document.assert_called_once()
        self.mock_chroma.update_document.assert_not_called()

    def test_get_all_compatibility_scores(self):
        """Test retrieving all compatibility scores."""
        # Mock get_all_documents to return a list of mock documents
        self.mock_chroma.get_all_documents.return_value = [
            {"metadata": {"tech_stack_a": ["Python"], "tech_stack_b": ["Django"], "score": 0.8}},
            {"metadata": {"tech_stack_a": ["JavaScript"], "tech_stack_b": ["React"], "score": 0.7}},
        ]

        scores = self.matrix.get_all_compatibility_scores()

        assert len(scores) == 2
        assert scores[0]["tech_stack_a"] == ["Python"]
        assert scores[0]["score"] == 0.8
        assert scores[1]["tech_stack_b"] == ["React"]
        assert scores[1]["score"] == 0.7

    def test_get_all_compatibility_scores_unavailable(self):
        """Test retrieving all scores when ChromaDB is unavailable."""
        self.mock_chroma.is_available.return_value = False

        scores = self.matrix.get_all_compatibility_scores()

        assert scores == []
        self.mock_chroma.get_all_documents.assert_not_called()

    def test_search_compatibility(self):
        """Test searching for compatibility with a specific tech stack."""
        query_stack = ["Python"]

        # Mock get_all_compatibility_scores to return test data
        self.matrix.get_all_compatibility_scores = Mock(return_value=[
            {"tech_stack_a": ["Python"], "tech_stack_b": ["Django"], "score": 0.8},
            {"tech_stack_a": ["JavaScript"], "tech_stack_b": ["React"], "score": 0.7},
            {"tech_stack_a": ["Python"], "tech_stack_b": ["Flask"], "score": 0.9}
        ])

        results = self.matrix.search_compatibility(query_stack, limit=5, min_score=0.0)

        # Should find 2 results with Python
        assert len(results) == 2
        assert all("Python" in (r["tech_stack_a"] + r["tech_stack_b"]) for r in results)


if __name__ == "__main__":
    pytest.main([__file__])
