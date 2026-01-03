"""
UCKN Personalized Ranking Atom

Provides personalized search result ranking based on user history, preferences,
and behavioral patterns to improve search relevance for individual users.
"""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any


class PersonalizedRanking:
    """
    Manages personalized ranking of search results based on user behavior.

    Features:
    - User interaction tracking (clicks, views, ratings)
    - Technology preference learning
    - Pattern usage history
    - Temporal decay of preferences
    """

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)
        self.user_profiles = {}
        self.interaction_weights = {
            "view": 1.0,
            "click": 2.0,
            "download": 3.0,
            "rate": 4.0,
            "share": 2.5,
            "bookmark": 3.5,
        }

    def track_interaction(
        self,
        user_id: str,
        pattern_id: str,
        interaction_type: str,
        pattern_metadata: dict[str, Any] | None = None,
        rating: float | None = None,
    ) -> None:
        """
        Track user interaction with a pattern.

        Args:
            user_id: Unique user identifier
            pattern_id: Pattern that was interacted with
            interaction_type: Type of interaction (view, click, download, rate, etc.)
            pattern_metadata: Metadata of the pattern
            rating: Optional rating if interaction_type is 'rate'
        """
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                "interactions": [],
                "technology_preferences": defaultdict(float),
                "pattern_type_preferences": defaultdict(float),
                "complexity_preferences": defaultdict(float),
                "language_preferences": defaultdict(float),
                "successful_patterns": set(),
                "bookmarked_patterns": set(),
                "last_activity": None,
            }

        profile = self.user_profiles[user_id]

        # Record the interaction
        interaction = {
            "pattern_id": pattern_id,
            "type": interaction_type,
            "timestamp": datetime.now(),
            "metadata": pattern_metadata or {},
            "rating": rating,
        }
        profile["interactions"].append(interaction)
        profile["last_activity"] = datetime.now()

        # Update preferences based on interaction
        if pattern_metadata:
            weight = self.interaction_weights.get(interaction_type, 1.0)

            # Apply rating multiplier
            if rating:
                weight *= rating / 5.0  # Assume 5-star rating scale

            # Update technology preferences
            tech_stack = pattern_metadata.get("technology_stack", [])
            if isinstance(tech_stack, str):
                tech_stack = [tech_stack]
            for tech in tech_stack:
                profile["technology_preferences"][tech.lower()] += weight

            # Update pattern type preferences
            pattern_type = pattern_metadata.get(
                "pattern_type", pattern_metadata.get("type")
            )
            if pattern_type:
                profile["pattern_type_preferences"][pattern_type] += weight

            # Update complexity preferences
            complexity = pattern_metadata.get("complexity")
            if complexity:
                profile["complexity_preferences"][complexity] += weight

            # Update language preferences
            language = pattern_metadata.get(
                "language", pattern_metadata.get("programming_language")
            )
            if language:
                profile["language_preferences"][language.lower()] += weight

        # Track special interactions
        if interaction_type == "bookmark":
            profile["bookmarked_patterns"].add(pattern_id)
        elif interaction_type == "rate" and rating and rating >= 4.0:
            profile["successful_patterns"].add(pattern_id)

    def personalize_ranking(
        self, user_id: str, search_results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Re-rank search results based on user preferences.

        Args:
            user_id: User identifier
            search_results: List of search results to re-rank

        Returns:
            Re-ranked search results with personalization scores
        """
        if user_id not in self.user_profiles or not search_results:
            return search_results

        profile = self.user_profiles[user_id]

        # Calculate personalization scores for each result
        personalized_results = []
        for result in search_results:
            metadata = result.get("metadata", {})
            base_score = result.get("similarity_score", 0.0)

            personalization_score = self._calculate_personalization_score(
                metadata, profile
            )

            # Combine base score with personalization (weighted average)
            combined_score = 0.7 * base_score + 0.3 * personalization_score

            result_copy = result.copy()
            result_copy["personalization_score"] = personalization_score
            result_copy["combined_score"] = combined_score

            personalized_results.append(result_copy)

        # Sort by combined score
        personalized_results.sort(key=lambda x: x["combined_score"], reverse=True)

        return personalized_results

    def _calculate_personalization_score(
        self, pattern_metadata: dict[str, Any], user_profile: dict[str, Any]
    ) -> float:
        """
        Calculate personalization score for a pattern based on user preferences.
        """
        score_components = []

        # Technology stack preference score
        tech_prefs = user_profile.get("technology_preferences", {})
        if tech_prefs:
            pattern_techs = pattern_metadata.get("technology_stack", [])
            if isinstance(pattern_techs, str):
                pattern_techs = [pattern_techs]

            tech_score = 0.0
            for tech in pattern_techs:
                tech_score += tech_prefs.get(tech.lower(), 0.0)

            if tech_score > 0 and tech_prefs:
                tech_score = min(tech_score / max(tech_prefs.values()), 1.0)
                score_components.append(tech_score)

        # Pattern type preference score
        type_prefs = user_profile.get("pattern_type_preferences", {})
        if type_prefs:
            pattern_type = pattern_metadata.get(
                "pattern_type", pattern_metadata.get("type")
            )
            if pattern_type:
                type_score = type_prefs.get(pattern_type, 0.0)
                type_score = min(type_score / max(type_prefs.values()), 1.0)
                score_components.append(type_score)

        return (
            sum(score_components) / len(score_components) if score_components else 0.5
        )
