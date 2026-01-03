"""
UCKN Pattern Recommendation Engine Organism

Provides intelligent pattern recommendations based on project context and technology stack.
Integrates multiple components to deliver personalized, context-aware suggestions.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..atoms.project_dna_fingerprinter import ProjectDNAFingerprinter
from ..atoms.semantic_search_engine import SemanticSearchEngine
from ..molecules.pattern_analytics import PatternAnalytics
from ..molecules.pattern_manager import PatternManager
from ..molecules.tech_stack_compatibility_matrix import TechStackCompatibilityMatrix


class RecommendationType(Enum):
    """Types of pattern recommendations"""

    SETUP = "setup"
    ISSUE_RESOLUTION = "issue_resolution"
    BEST_PRACTICE = "best_practice"
    PROACTIVE = "proactive"


@dataclass
class Recommendation:
    """A pattern recommendation with metadata"""

    pattern_id: str
    pattern_content: str
    recommendation_type: RecommendationType
    confidence_score: float
    compatibility_score: float
    success_rate: float
    relevance_score: float
    description: str
    metadata: dict[str, Any]


class PatternRecommendationEngine:
    """
    Intelligent pattern recommendation engine that provides context-aware suggestions
    based on project characteristics, technology stack, and user history.

    Features:
    - Content-based filtering using technology stack similarity
    - Collaborative filtering using success rates from similar projects
    - Context-aware ranking considering project characteristics
    - Multiple recommendation types (setup, issue resolution, best practices, proactive)
    """

    def __init__(
        self,
        dna_fingerprinter: ProjectDNAFingerprinter,
        semantic_search: SemanticSearchEngine,
        compatibility_matrix: TechStackCompatibilityMatrix,
        pattern_analytics: PatternAnalytics,
        pattern_manager: PatternManager,
    ):
        """
        Initialize the pattern recommendation engine.

        Args:
            dna_fingerprinter: Project DNA fingerprinter for technology analysis
            semantic_search: Semantic search engine for pattern retrieval
            compatibility_matrix: Technology stack compatibility matrix
            pattern_analytics: Pattern analytics for success metrics
            pattern_manager: Pattern manager for pattern retrieval
        """
        self.dna_fingerprinter = dna_fingerprinter
        self.semantic_search = semantic_search
        self.compatibility_matrix = compatibility_matrix
        self.pattern_analytics = pattern_analytics
        self.pattern_manager = pattern_manager
        self._logger = logging.getLogger(__name__)

    def is_available(self) -> bool:
        """Check if all required components are available."""
        return all(
            [
                self.dna_fingerprinter,
                self.semantic_search and self.semantic_search.is_available(),
                self.compatibility_matrix and self.compatibility_matrix.is_available(),
                self.pattern_analytics,
                self.pattern_manager,
            ]
        )

    def get_setup_recommendations(
        self, project_path: str, limit: int = 10
    ) -> list[Recommendation]:
        """
        Get setup recommendations for initial project configuration.

        Args:
            project_path: Path to the project directory
            limit: Maximum number of recommendations to return

        Returns:
            List of setup recommendations
        """
        if not self.is_available():
            self._logger.warning("Recommendation engine not fully available")
            return []

        try:
            # Generate project DNA fingerprint
            fingerprint = self.dna_fingerprinter.generate_fingerprint(project_path)
            tech_stack = fingerprint.get("languages", []) + fingerprint.get(
                "frameworks", []
            )

            # Search for setup patterns
            setup_patterns = self._search_patterns_by_type(
                "setup", tech_stack, limit * 2
            )

            # Rank and filter recommendations
            recommendations = self._create_recommendations(
                setup_patterns, RecommendationType.SETUP, fingerprint, tech_stack
            )

            return self._rank_recommendations(recommendations, fingerprint)[:limit]

        except Exception as e:
            self._logger.error(f"Error generating setup recommendations: {e}")
            return []

    def get_issue_resolution_recommendations(
        self, error_context: str, project_path: str, limit: int = 5
    ) -> list[Recommendation]:
        """
        Get recommendations for resolving specific issues or errors.

        Args:
            error_context: Description of the error or issue
            project_path: Path to the project directory
            limit: Maximum number of recommendations to return

        Returns:
            List of issue resolution recommendations
        """
        if not self.is_available():
            self._logger.warning("Recommendation engine not fully available")
            return []

        try:
            # Generate project DNA fingerprint
            fingerprint = self.dna_fingerprinter.generate_fingerprint(project_path)
            tech_stack = fingerprint.get("languages", []) + fingerprint.get(
                "frameworks", []
            )

            # Search for error resolution patterns using semantic search
            search_results = self.semantic_search.search_by_error(
                error_message=error_context, tech_stack=tech_stack, limit=limit * 2
            )

            # Convert search results to patterns
            issue_patterns = self._convert_search_results_to_patterns(search_results)

            # Create and rank recommendations
            recommendations = self._create_recommendations(
                issue_patterns,
                RecommendationType.ISSUE_RESOLUTION,
                fingerprint,
                tech_stack,
            )

            return self._rank_recommendations(recommendations, fingerprint)[:limit]

        except Exception as e:
            self._logger.error(
                f"Error generating issue resolution recommendations: {e}"
            )
            return []

    def get_best_practice_recommendations(
        self, project_path: str, limit: int = 8
    ) -> list[Recommendation]:
        """
        Get best practice recommendations for the technology stack.

        Args:
            project_path: Path to the project directory
            limit: Maximum number of recommendations to return

        Returns:
            List of best practice recommendations
        """
        if not self.is_available():
            self._logger.warning("Recommendation engine not fully available")
            return []

        try:
            # Generate project DNA fingerprint
            fingerprint = self.dna_fingerprinter.generate_fingerprint(project_path)
            tech_stack = fingerprint.get("languages", []) + fingerprint.get(
                "frameworks", []
            )

            # Search for high-success patterns for this tech stack
            best_practice_patterns = self._search_high_success_patterns(
                tech_stack, limit * 2
            )

            # Create and rank recommendations
            recommendations = self._create_recommendations(
                best_practice_patterns,
                RecommendationType.BEST_PRACTICE,
                fingerprint,
                tech_stack,
            )

            return self._rank_recommendations(recommendations, fingerprint)[:limit]

        except Exception as e:
            self._logger.error(f"Error generating best practice recommendations: {e}")
            return []

    def get_proactive_recommendations(
        self, project_path: str, limit: int = 6
    ) -> list[Recommendation]:
        """
        Get proactive recommendations to prevent common issues.

        Args:
            project_path: Path to the project directory
            limit: Maximum number of recommendations to return

        Returns:
            List of proactive recommendations
        """
        if not self.is_available():
            self._logger.warning("Recommendation engine not fully available")
            return []

        try:
            # Generate project DNA fingerprint
            fingerprint = self.dna_fingerprinter.generate_fingerprint(project_path)
            tech_stack = fingerprint.get("languages", []) + fingerprint.get(
                "frameworks", []
            )

            # Search for prevention patterns
            proactive_patterns = self._search_patterns_by_type(
                "prevention", tech_stack, limit * 2
            )

            # Create and rank recommendations
            recommendations = self._create_recommendations(
                proactive_patterns,
                RecommendationType.PROACTIVE,
                fingerprint,
                tech_stack,
            )

            return self._rank_recommendations(recommendations, fingerprint)[:limit]

        except Exception as e:
            self._logger.error(f"Error generating proactive recommendations: {e}")
            return []

    def get_comprehensive_recommendations(
        self,
        project_path: str,
        error_context: str | None = None,
        user_history: list[str] | None = None,
    ) -> dict[str, list[Recommendation]]:
        """
        Get comprehensive recommendations across all types.

        Args:
            project_path: Path to the project directory
            error_context: Optional error context for issue resolution
            user_history: Optional user history for personalization

        Returns:
            Dictionary with recommendation types as keys and recommendation lists as values
        """
        recommendations = {
            "setup": self.get_setup_recommendations(project_path, limit=5),
            "best_practices": self.get_best_practice_recommendations(
                project_path, limit=5
            ),
            "proactive": self.get_proactive_recommendations(project_path, limit=3),
        }

        if error_context:
            recommendations["issue_resolution"] = (
                self.get_issue_resolution_recommendations(
                    error_context, project_path, limit=3
                )
            )

        # Apply personalization if user history is provided
        if user_history:
            for rec_type in recommendations:
                recommendations[rec_type] = self.personalize_recommendations(
                    recommendations[rec_type], user_history
                )

        return recommendations

    def _search_patterns_by_type(
        self, pattern_type: str, tech_stack: list[str], limit: int
    ) -> list[dict[str, Any]]:
        """Search for patterns by type and technology stack."""
        try:
            # Use semantic search to find patterns of specific type
            search_results = self.semantic_search.search_by_text(
                query=f"{pattern_type} patterns", tech_stack=tech_stack, limit=limit
            )
            return self._convert_search_results_to_patterns(search_results)
        except Exception as e:
            self._logger.error(f"Error searching patterns by type {pattern_type}: {e}")
            return []

    def _search_high_success_patterns(
        self, tech_stack: list[str], limit: int
    ) -> list[dict[str, Any]]:
        """Search for patterns with high success rates for the given tech stack."""
        try:
            # Get all patterns and filter by success rate
            all_patterns = self.pattern_manager.search_patterns(
                query="best practices",
                limit=limit * 3,
                metadata_filter={"tech_stack": tech_stack[0] if tech_stack else None},
            )

            # Filter patterns with high success rates
            high_success_patterns = []
            for pattern in all_patterns:
                metadata = pattern.get("metadata", {})
                success_metrics = metadata.get("success_metrics", {})
                success_rate = success_metrics.get("success_rate", 0.0)

                if success_rate >= 0.8:  # High success threshold
                    high_success_patterns.append(pattern)

            return high_success_patterns[:limit]

        except Exception as e:
            self._logger.error(f"Error searching high success patterns: {e}")
            return []

    def _convert_search_results_to_patterns(
        self, search_results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Convert semantic search results to pattern format."""
        patterns = []
        for result in search_results:
            pattern = {
                "pattern_id": result.get("id", "unknown"),
                "content": result.get("document", ""),
                "metadata": result.get("metadata", {}),
                "similarity_score": result.get("similarity_score", 0.0),
            }
            patterns.append(pattern)
        return patterns

    def _create_recommendations(
        self,
        patterns: list[dict[str, Any]],
        rec_type: RecommendationType,
        fingerprint: dict[str, Any],
        tech_stack: list[str],
    ) -> list[Recommendation]:
        """Create recommendation objects from patterns."""
        recommendations = []

        for pattern in patterns:
            try:
                # Calculate compatibility score
                compatibility_score = self._calculate_compatibility_score(
                    pattern, tech_stack
                )

                # Get success rate from analytics
                success_rate = self._get_pattern_success_rate(pattern.get("pattern_id"))

                # Calculate relevance score
                relevance_score = pattern.get("similarity_score", 0.5)

                # Calculate overall confidence score
                confidence_score = self._calculate_confidence_score(
                    compatibility_score, success_rate, relevance_score
                )

                recommendation = Recommendation(
                    pattern_id=pattern.get("pattern_id", ""),
                    pattern_content=pattern.get("content", ""),
                    recommendation_type=rec_type,
                    confidence_score=confidence_score,
                    compatibility_score=compatibility_score,
                    success_rate=success_rate,
                    relevance_score=relevance_score,
                    description=pattern.get("metadata", {}).get("description", ""),
                    metadata=pattern.get("metadata", {}),
                )

                recommendations.append(recommendation)

            except Exception as e:
                self._logger.error(f"Error creating recommendation from pattern: {e}")
                continue

        return recommendations

    def _calculate_compatibility_score(
        self, pattern: dict[str, Any], tech_stack: list[str]
    ) -> float:
        """Calculate compatibility score between pattern and tech stack."""
        try:
            pattern_metadata = pattern.get("metadata", {})
            pattern_tech_stack = pattern_metadata.get("tech_stack", {})

            # Extract tech stack from pattern metadata
            pattern_technologies = []
            if isinstance(pattern_tech_stack, dict):
                for category in ["languages", "frameworks", "testing", "ci_cd"]:
                    technologies = pattern_tech_stack.get(category, [])
                    if isinstance(technologies, list):
                        pattern_technologies.extend(technologies)

            if not pattern_technologies or not tech_stack:
                return 0.5  # Neutral score if no tech stack info

            # Calculate intersection over union
            set_pattern = {t.lower() for t in pattern_technologies}
            set_project = {t.lower() for t in tech_stack}

            intersection = set_pattern & set_project
            union = set_pattern | set_project

            return len(intersection) / len(union) if union else 0.5

        except Exception as e:
            self._logger.error(f"Error calculating compatibility score: {e}")
            return 0.5

    def _get_pattern_success_rate(self, pattern_id: str) -> float:
        """Get success rate for a pattern from analytics."""
        try:
            if not pattern_id:
                return 0.5

            # Get pattern metrics from analytics
            metrics = self.pattern_analytics.get_pattern_metrics(pattern_id)
            return metrics.get("success_rate", 0.5)

        except Exception as e:
            self._logger.error(f"Error getting pattern success rate: {e}")
            return 0.5

    def _calculate_confidence_score(
        self, compatibility_score: float, success_rate: float, relevance_score: float
    ) -> float:
        """Calculate overall confidence score for a recommendation."""
        # Weighted average of different factors
        weights = {"compatibility": 0.4, "success_rate": 0.35, "relevance": 0.25}

        confidence = (
            compatibility_score * weights["compatibility"]
            + success_rate * weights["success_rate"]
            + relevance_score * weights["relevance"]
        )

        return min(max(confidence, 0.0), 1.0)  # Clamp to [0, 1]

    def _rank_recommendations(
        self, recommendations: list[Recommendation], context: dict[str, Any]
    ) -> list[Recommendation]:
        """Rank recommendations by confidence score and other factors."""
        return sorted(
            recommendations,
            key=lambda r: (r.confidence_score, r.success_rate, r.compatibility_score),
            reverse=True,
        )

    def personalize_recommendations(
        self, recommendations: list[Recommendation], user_history: list[str]
    ) -> list[Recommendation]:
        """
        Personalize recommendations based on user history.

        Args:
            recommendations: List of recommendations to personalize
            user_history: List of pattern IDs the user has previously used

        Returns:
            Personalized list of recommendations
        """
        if not user_history:
            return recommendations

        # Boost recommendations for patterns similar to user's history
        for recommendation in recommendations:
            # Simple personalization: boost if pattern type matches history
            if recommendation.pattern_id in user_history:
                # Boost confidence for patterns user has used before
                recommendation.confidence_score = min(
                    recommendation.confidence_score * 1.2, 1.0
                )

        # Re-rank with personalized scores
        return sorted(recommendations, key=lambda r: r.confidence_score, reverse=True)
