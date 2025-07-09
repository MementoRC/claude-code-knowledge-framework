"""
UCKN Search Suggestion Engine Atom

Provides intelligent search suggestions, autocomplete, and query enhancement
based on user behavior, popular searches, and content analysis.
"""

import logging
import re
from collections import defaultdict
from logging import Logger
from typing import Any, Optional


class SearchSuggestionEngine:
    """
    Manages search suggestions and autocomplete functionality.

    Features:
    - Query autocomplete based on popular searches
    - Spelling correction suggestions
    - Related search suggestions
    - Technology-aware suggestions
    """

    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.query_history = defaultdict(int)
        self.successful_queries = defaultdict(int)
        self.technology_keywords = {
            "python",
            "javascript",
            "java",
            "react",
            "django",
            "flask",
            "node",
            "angular",
            "vue",
            "typescript",
            "go",
            "rust",
            "kotlin",
            "swift",
            "docker",
            "kubernetes",
            "aws",
            "azure",
            "gcp",
            "terraform",
            "mongodb",
            "postgresql",
            "mysql",
            "redis",
            "elasticsearch",
        }
        self.common_terms = {
            "error",
            "bug",
            "fix",
            "solution",
            "pattern",
            "example",
            "tutorial",
            "best",
            "practice",
            "performance",
            "security",
            "testing",
            "deployment",
        }

    def track_query(
        self, query: str, success: bool = False, result_count: int = 0
    ) -> None:
        """Track a search query for suggestion improvement."""
        normalized_query = self._normalize_query(query)
        self.query_history[normalized_query] += 1

        if success or result_count > 0:
            self.successful_queries[normalized_query] += 1

    def get_autocomplete_suggestions(
        self, partial_query: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Get autocomplete suggestions for a partial query."""
        if not partial_query or len(partial_query) < 2:
            return []

        normalized_partial = self._normalize_query(partial_query).lower()
        suggestions = []

        # Find matching queries from history
        for query, count in self.query_history.items():
            if query.lower().startswith(normalized_partial):
                success_rate = self.successful_queries.get(query, 0) / count
                suggestions.append(
                    {
                        "text": query,
                        "type": "history",
                        "score": count * (1 + success_rate),
                    }
                )

        # Add technology-based suggestions
        for tech in self.technology_keywords:
            if tech.startswith(normalized_partial):
                suggestions.append(
                    {
                        "text": tech,
                        "type": "technology",
                        "score": 10 * 0.8,  # Boost technology suggestions
                    }
                )

        # Sort by score and remove duplicates
        unique_suggestions = {}
        for suggestion in suggestions:
            text = suggestion["text"]
            if (
                text not in unique_suggestions
                or suggestion["score"] > unique_suggestions[text]["score"]
            ):
                unique_suggestions[text] = suggestion

        sorted_suggestions = sorted(
            unique_suggestions.values(), key=lambda x: x["score"], reverse=True
        )

        return sorted_suggestions[:limit]

    def get_related_suggestions(self, query: str, limit: int = 3) -> list[str]:
        """Get related search suggestions for a given query."""
        normalized_query = self._normalize_query(query).lower()

        # Extract key terms from the query
        query_terms = set(self._extract_terms(normalized_query))

        # Find queries with overlapping terms
        candidates = []
        for historical_query, count in self.query_history.items():
            if historical_query.lower() == normalized_query:
                continue

            historical_terms = set(self._extract_terms(historical_query.lower()))
            overlap = len(query_terms & historical_terms)

            if overlap > 0:
                success_rate = self.successful_queries.get(historical_query, 0) / count
                similarity_score = overlap / len(query_terms | historical_terms)
                candidates.append(
                    {
                        "query": historical_query,
                        "score": similarity_score * count * (1 + success_rate),
                    }
                )

        # Sort candidates and take top suggestions
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return [c["query"] for c in candidates[:limit]]

    def _normalize_query(self, query: str) -> str:
        """Normalize a query for consistent processing."""
        return re.sub(r"\s+", " ", query.strip())

    def _extract_terms(self, query: str) -> list[str]:
        """Extract meaningful terms from a query."""
        terms = re.findall(r"\w+", query.lower())
        return [term for term in terms if len(term) >= 2]
