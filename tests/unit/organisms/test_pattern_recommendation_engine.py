"""
Test PatternRecommendationEngine functionality
"""

from unittest.mock import Mock

import pytest

from src.uckn.core.organisms.pattern_recommendation_engine import (
    PatternRecommendationEngine,
    Recommendation,
    RecommendationType,
)


class TestPatternRecommendationEngine:
    """Test PatternRecommendationEngine functionality"""

    def setup_method(self):
        """Setup test fixtures for each test method."""
        # Mock all dependencies
        self.mock_dna_fingerprinter = Mock()
        self.mock_semantic_search = Mock()
        self.mock_compatibility_matrix = Mock()
        self.mock_pattern_analytics = Mock()
        self.mock_pattern_manager = Mock()

        # Configure mocks to be available by default
        self.mock_semantic_search.is_available.return_value = True
        self.mock_compatibility_matrix.is_available.return_value = True

        # Initialize the recommendation engine
        self.engine = PatternRecommendationEngine(
            dna_fingerprinter=self.mock_dna_fingerprinter,
            semantic_search=self.mock_semantic_search,
            compatibility_matrix=self.mock_compatibility_matrix,
            pattern_analytics=self.mock_pattern_analytics,
            pattern_manager=self.mock_pattern_manager,
        )

    def test_initialization(self):
        """Test PatternRecommendationEngine initializes correctly."""
        assert self.engine.dna_fingerprinter == self.mock_dna_fingerprinter
        assert self.engine.semantic_search == self.mock_semantic_search
        assert self.engine.compatibility_matrix == self.mock_compatibility_matrix
        assert self.engine.pattern_analytics == self.mock_pattern_analytics
        assert self.engine.pattern_manager == self.mock_pattern_manager

    def test_is_available_true(self):
        """Test is_available returns True when all components are available."""
        assert self.engine.is_available() is True

    def test_is_available_false_missing_component(self):
        """Test is_available returns False when a component is missing."""
        self.mock_semantic_search.is_available.return_value = False
        assert self.engine.is_available() is False

    def test_is_available_false_none_component(self):
        """Test is_available returns False when a component is None."""
        engine = PatternRecommendationEngine(
            dna_fingerprinter=None,
            semantic_search=self.mock_semantic_search,
            compatibility_matrix=self.mock_compatibility_matrix,
            pattern_analytics=self.mock_pattern_analytics,
            pattern_manager=self.mock_pattern_manager,
        )
        assert engine.is_available() is False

    def test_get_setup_recommendations_success(self):
        """Test getting setup recommendations successfully."""
        # Mock DNA fingerprinting
        mock_fingerprint = {
            "languages": ["Python"],
            "frameworks": ["FastAPI"],
            "testing": ["pytest"],
        }
        self.mock_dna_fingerprinter.generate_fingerprint.return_value = mock_fingerprint

        # Mock search results
        mock_search_results = [
            {
                "id": "setup_1",
                "document": "Python FastAPI setup pattern",
                "metadata": {
                    "description": "Setup FastAPI with Python",
                    "tech_stack": {"languages": ["Python"], "frameworks": ["FastAPI"]},
                },
                "similarity_score": 0.9,
            }
        ]
        self.mock_semantic_search.search_by_text.return_value = mock_search_results

        # Mock pattern analytics
        self.mock_pattern_analytics.get_pattern_metrics.return_value = {
            "success_rate": 0.85
        }

        recommendations = self.engine.get_setup_recommendations(
            "/test/project", limit=5
        )

        assert len(recommendations) > 0
        assert recommendations[0].recommendation_type == RecommendationType.SETUP
        assert recommendations[0].pattern_id == "setup_1"
        self.mock_dna_fingerprinter.generate_fingerprint.assert_called_once_with(
            "/test/project"
        )

    def test_get_setup_recommendations_unavailable(self):
        """Test getting setup recommendations when engine is unavailable."""
        self.mock_semantic_search.is_available.return_value = False

        recommendations = self.engine.get_setup_recommendations("/test/project")

        assert recommendations == []

    def test_get_issue_resolution_recommendations_success(self):
        """Test getting issue resolution recommendations successfully."""
        # Mock DNA fingerprinting
        mock_fingerprint = {"languages": ["Python"], "frameworks": ["Django"]}
        self.mock_dna_fingerprinter.generate_fingerprint.return_value = mock_fingerprint

        # Mock search results
        mock_search_results = [
            {
                "id": "error_1",
                "document": "Django import error resolution",
                "metadata": {
                    "description": "Fix Django import errors",
                    "tech_stack": {"languages": ["Python"], "frameworks": ["Django"]},
                },
                "similarity_score": 0.8,
            }
        ]
        self.mock_semantic_search.search_by_error.return_value = mock_search_results

        # Mock pattern analytics
        self.mock_pattern_analytics.get_pattern_metrics.return_value = {
            "success_rate": 0.9
        }

        recommendations = self.engine.get_issue_resolution_recommendations(
            "ImportError: No module named 'django'", "/test/project", limit=3
        )

        assert len(recommendations) > 0
        assert (
            recommendations[0].recommendation_type
            == RecommendationType.ISSUE_RESOLUTION
        )
        assert recommendations[0].pattern_id == "error_1"
        self.mock_semantic_search.search_by_error.assert_called_once()

    def test_get_best_practice_recommendations_success(self):
        """Test getting best practice recommendations successfully."""
        # Mock DNA fingerprinting
        mock_fingerprint = {"languages": ["Python"], "frameworks": ["FastAPI"]}
        self.mock_dna_fingerprinter.generate_fingerprint.return_value = mock_fingerprint

        # Mock high success patterns
        mock_patterns = [
            {
                "pattern_id": "best_1",
                "content": "Python testing best practices",
                "metadata": {
                    "description": "Best practices for Python testing",
                    "success_metrics": {"success_rate": 0.95},
                },
                "similarity_score": 0.85,
            }
        ]
        self.engine._search_high_success_patterns = Mock(return_value=mock_patterns)

        # Mock pattern analytics
        self.mock_pattern_analytics.get_pattern_metrics.return_value = {
            "success_rate": 0.95
        }

        recommendations = self.engine.get_best_practice_recommendations(
            "/test/project", limit=5
        )

        assert len(recommendations) > 0
        assert (
            recommendations[0].recommendation_type == RecommendationType.BEST_PRACTICE
        )
        assert recommendations[0].pattern_id == "best_1"

    def test_get_proactive_recommendations_success(self):
        """Test getting proactive recommendations successfully."""
        # Mock DNA fingerprinting
        mock_fingerprint = {"languages": ["Python"], "frameworks": ["Flask"]}
        self.mock_dna_fingerprinter.generate_fingerprint.return_value = mock_fingerprint

        # Mock search results
        mock_search_results = [
            {
                "id": "proactive_1",
                "document": "Prevent common Flask security issues",
                "metadata": {
                    "description": "Security patterns for Flask",
                    "tech_stack": {"languages": ["Python"], "frameworks": ["Flask"]},
                },
                "similarity_score": 0.8,
            }
        ]
        self.mock_semantic_search.search_by_text.return_value = mock_search_results

        # Mock pattern analytics
        self.mock_pattern_analytics.get_pattern_metrics.return_value = {
            "success_rate": 0.8
        }

        recommendations = self.engine.get_proactive_recommendations(
            "/test/project", limit=3
        )

        assert len(recommendations) > 0
        assert recommendations[0].recommendation_type == RecommendationType.PROACTIVE
        assert recommendations[0].pattern_id == "proactive_1"

    def test_get_comprehensive_recommendations_without_error(self):
        """Test getting comprehensive recommendations without error context."""
        # Mock setup recommendations
        self.engine.get_setup_recommendations = Mock(
            return_value=[
                self._create_mock_recommendation("setup_1", RecommendationType.SETUP)
            ]
        )

        # Mock best practice recommendations
        self.engine.get_best_practice_recommendations = Mock(
            return_value=[
                self._create_mock_recommendation(
                    "best_1", RecommendationType.BEST_PRACTICE
                )
            ]
        )

        # Mock proactive recommendations
        self.engine.get_proactive_recommendations = Mock(
            return_value=[
                self._create_mock_recommendation(
                    "proactive_1", RecommendationType.PROACTIVE
                )
            ]
        )

        recommendations = self.engine.get_comprehensive_recommendations("/test/project")

        assert "setup" in recommendations
        assert "best_practices" in recommendations
        assert "proactive" in recommendations
        assert "issue_resolution" not in recommendations
        assert len(recommendations["setup"]) == 1
        assert len(recommendations["best_practices"]) == 1
        assert len(recommendations["proactive"]) == 1

    def test_get_comprehensive_recommendations_with_error(self):
        """Test getting comprehensive recommendations with error context."""
        # Mock all recommendation types
        self.engine.get_setup_recommendations = Mock(return_value=[])
        self.engine.get_best_practice_recommendations = Mock(return_value=[])
        self.engine.get_proactive_recommendations = Mock(return_value=[])
        self.engine.get_issue_resolution_recommendations = Mock(
            return_value=[
                self._create_mock_recommendation(
                    "error_1", RecommendationType.ISSUE_RESOLUTION
                )
            ]
        )

        recommendations = self.engine.get_comprehensive_recommendations(
            "/test/project", error_context="ImportError occurred"
        )

        assert "issue_resolution" in recommendations
        assert len(recommendations["issue_resolution"]) == 1
        self.engine.get_issue_resolution_recommendations.assert_called_once_with(
            "ImportError occurred", "/test/project", limit=3
        )

    def test_personalize_recommendations_with_history(self):
        """Test personalizing recommendations with user history."""
        recommendations = [
            self._create_mock_recommendation(
                "pattern_1", RecommendationType.SETUP, confidence=0.7
            ),
            self._create_mock_recommendation(
                "pattern_2", RecommendationType.SETUP, confidence=0.8
            ),
        ]

        user_history = ["pattern_1"]

        personalized = self.engine.personalize_recommendations(
            recommendations, user_history
        )

        # pattern_1 should have boosted confidence score
        pattern_1_rec = next(r for r in personalized if r.pattern_id == "pattern_1")
        pattern_2_rec = next(r for r in personalized if r.pattern_id == "pattern_2")

        assert pattern_1_rec.confidence_score > 0.7  # Should be boosted
        assert pattern_2_rec.confidence_score == 0.8  # Should remain same

        # Recommendations should be re-sorted by confidence
        assert (
            personalized[0].pattern_id == "pattern_1"
        )  # Higher confidence after boost

    def test_personalize_recommendations_without_history(self):
        """Test personalizing recommendations without user history."""
        recommendations = [
            self._create_mock_recommendation("pattern_1", RecommendationType.SETUP),
            self._create_mock_recommendation("pattern_2", RecommendationType.SETUP),
        ]

        personalized = self.engine.personalize_recommendations(recommendations, [])

        assert personalized == recommendations  # Should remain unchanged

    def test_calculate_compatibility_score(self):
        """Test calculating compatibility score between pattern and tech stack."""
        pattern = {
            "metadata": {
                "tech_stack": {"languages": ["Python"], "frameworks": ["Django"]}
            }
        }
        tech_stack = ["Python", "Django"]

        score = self.engine._calculate_compatibility_score(pattern, tech_stack)

        assert score == 1.0  # Perfect match

    def test_calculate_compatibility_score_partial_match(self):
        """Test calculating compatibility score with partial match."""
        pattern = {
            "metadata": {
                "tech_stack": {"languages": ["Python"], "frameworks": ["Django"]}
            }
        }
        tech_stack = ["Python", "FastAPI"]  # Different framework

        score = self.engine._calculate_compatibility_score(pattern, tech_stack)

        assert 0.0 < score < 1.0  # Partial match

    def test_calculate_confidence_score(self):
        """Test calculating overall confidence score."""
        compatibility_score = 0.8
        success_rate = 0.9
        relevance_score = 0.7

        confidence = self.engine._calculate_confidence_score(
            compatibility_score, success_rate, relevance_score
        )

        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.7  # Should be high given good input scores

    def test_rank_recommendations(self):
        """Test ranking recommendations by confidence and other factors."""
        recommendations = [
            self._create_mock_recommendation(
                "low", RecommendationType.SETUP, confidence=0.5
            ),
            self._create_mock_recommendation(
                "high", RecommendationType.SETUP, confidence=0.9
            ),
            self._create_mock_recommendation(
                "medium", RecommendationType.SETUP, confidence=0.7
            ),
        ]

        ranked = self.engine._rank_recommendations(recommendations, {})

        assert ranked[0].pattern_id == "high"
        assert ranked[1].pattern_id == "medium"
        assert ranked[2].pattern_id == "low"

    def _create_mock_recommendation(
        self, pattern_id: str, rec_type: RecommendationType, confidence: float = 0.8
    ) -> Recommendation:
        """Helper to create a mock recommendation."""
        return Recommendation(
            pattern_id=pattern_id,
            pattern_content=f"Content for {pattern_id}",
            recommendation_type=rec_type,
            confidence_score=confidence,
            compatibility_score=0.8,
            success_rate=0.85,
            relevance_score=0.75,
            description=f"Description for {pattern_id}",
            metadata={},
        )


if __name__ == "__main__":
    pytest.main([__file__])
