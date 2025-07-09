"""
UCKN Advanced Search Engine Molecule

Orchestrates advanced search capabilities by integrating multiple search atoms
including semantic search, query parsing, faceted filtering, and personalized ranking.
"""

import logging
from datetime import datetime
from logging import Logger
from typing import Any, Optional

from ..atoms.faceted_search_manager import FacetedSearchManager
from ..atoms.personalized_ranking import PersonalizedRanking
from ..atoms.query_parser import QueryParser
from ..atoms.search_suggestion_engine import SearchSuggestionEngine
from ..atoms.semantic_search_engine import SemanticSearchEngine


class AdvancedSearchEngine:
    """
    Advanced search engine that combines semantic search with sophisticated
    filtering, ranking, and personalization capabilities.
    """

    def __init__(
        self,
        semantic_engine: Optional[SemanticSearchEngine] = None,
        query_parser: Optional[QueryParser] = None,
        faceted_manager: Optional[FacetedSearchManager] = None,
        personalized_ranking: Optional[PersonalizedRanking] = None,
        suggestion_engine: Optional[SearchSuggestionEngine] = None,
        logger: Optional[Logger] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)

        # Initialize component atoms
        self.semantic_engine = semantic_engine or SemanticSearchEngine()
        self.query_parser = query_parser or QueryParser()
        self.faceted_manager = faceted_manager or FacetedSearchManager()
        self.personalized_ranking = personalized_ranking or PersonalizedRanking()
        self.suggestion_engine = suggestion_engine or SearchSuggestionEngine()

    def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        filters: dict[str, Any] | None = None,
        limit: int = 20,
        enable_personalization: bool = True,
    ) -> dict[str, Any]:
        """
        Perform advanced search with all capabilities.
        """
        start_time = datetime.now()

        try:
            # Parse the query for complex boolean operations
            parsed_query = self.query_parser.parse_query(query)
            search_terms = self.query_parser.extract_terms(parsed_query)

            # Perform semantic search
            if search_terms:
                semantic_query = " ".join(search_terms[:5])  # Limit to top 5 terms
                results = self.semantic_engine.search_by_text(
                    semantic_query,
                    tech_stack=filters.get("technology_stack") if filters else None,
                    limit=limit * 2,  # Get more results for better filtering
                )
            else:
                results = []

            # Apply faceted filtering
            if filters:
                results = self.faceted_manager.apply_facet_filters(results, filters)

            # Apply personalized ranking if enabled
            if enable_personalization and user_id:
                results = self.personalized_ranking.personalize_ranking(
                    user_id, results
                )

            # Extract facets from results for dynamic filtering
            available_facets = self.faceted_manager.extract_facets(results)

            # Limit final results
            final_results = results[:limit]

            # Calculate search metadata
            search_time = (datetime.now() - start_time).total_seconds()

            # Track query for suggestions
            self.suggestion_engine.track_query(
                query, success=len(final_results) > 0, result_count=len(final_results)
            )

            return {
                "results": final_results,
                "total_count": len(results),
                "returned_count": len(final_results),
                "search_metadata": {
                    "query": query,
                    "parsed_query": parsed_query,
                    "search_terms": search_terms,
                    "filters_applied": filters or {},
                    "personalization_enabled": enable_personalization,
                    "search_time_ms": int(search_time * 1000),
                },
                "facets": available_facets,
                "suggestions": {
                    "related_queries": self.suggestion_engine.get_related_suggestions(
                        query
                    ),
                },
            }

        except Exception as e:
            self.logger.error(f"Error in advanced search: {e}")
            return {
                "results": [],
                "total_count": 0,
                "returned_count": 0,
                "error": str(e),
            }

    def get_autocomplete_suggestions(
        self, partial_query: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Get autocomplete suggestions for a partial query."""
        try:
            return self.suggestion_engine.get_autocomplete_suggestions(
                partial_query, limit
            )
        except Exception as e:
            self.logger.error(f"Error getting autocomplete suggestions: {e}")
            return []

    def track_user_interaction(
        self,
        user_id: str,
        pattern_id: str,
        interaction_type: str,
        pattern_metadata: dict[str, Any] | None = None,
        rating: Optional[float] = None,
    ) -> None:
        """Track user interaction for personalization improvement."""
        try:
            self.personalized_ranking.track_interaction(
                user_id=user_id,
                pattern_id=pattern_id,
                interaction_type=interaction_type,
                pattern_metadata=pattern_metadata,
                rating=rating,
            )
        except Exception as e:
            self.logger.error(f"Error tracking user interaction: {e}")
