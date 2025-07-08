"""
UCKN Faceted Search Manager Atom

Manages dynamic faceted search capabilities including technology stack filtering,
temporal filters, quality metrics, and other dynamic filters based on document metadata.
"""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Optional


class FacetedSearchManager:
    """
    Manages faceted search capabilities for UCKN knowledge patterns.

    Provides dynamic filtering based on:
    - Technology stack compatibility
    - Temporal filters (pattern age, update frequency)
    - Quality metrics (success rates, usage statistics)
    - Pattern complexity levels
    - Source/origin filters
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._facet_cache = {}
        self._cache_expiry = {}

    def extract_facets(self, documents: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Extract available facets from a collection of documents.

        Args:
            documents: List of documents with metadata

        Returns:
            Dictionary of facets with possible values and counts
        """
        facets = {
            "technology_stack": defaultdict(int),
            "complexity": defaultdict(int),
            "pattern_type": defaultdict(int),
            "success_rate_range": defaultdict(int),
            "age_range": defaultdict(int),
            "language": defaultdict(int),
            "framework": defaultdict(int),
            "source": defaultdict(int),
        }

        for doc in documents:
            metadata = doc.get("metadata", {})

            # Technology stack facets
            tech_stack = metadata.get("technology_stack", [])
            if isinstance(tech_stack, str):
                tech_stack = [tech_stack]
            for tech in tech_stack:
                facets["technology_stack"][tech.lower()] += 1

            # Complexity facets
            complexity = metadata.get("complexity", "unknown")
            facets["complexity"][complexity] += 1

            # Pattern type facets
            pattern_type = metadata.get("pattern_type", metadata.get("type", "unknown"))
            facets["pattern_type"][pattern_type] += 1

            # Success rate ranges
            success_rate = metadata.get("success_rate", 0.0)
            if isinstance(success_rate, (int, float)):
                if success_rate >= 0.9:
                    facets["success_rate_range"]["excellent (90%+)"] += 1
                elif success_rate >= 0.75:
                    facets["success_rate_range"]["good (75-89%)"] += 1
                elif success_rate >= 0.5:
                    facets["success_rate_range"]["moderate (50-74%)"] += 1
                else:
                    facets["success_rate_range"]["low (<50%)"] += 1

            # Age ranges
            created_at = metadata.get("created_at")
            if created_at:
                try:
                    if isinstance(created_at, str):
                        created_date = datetime.fromisoformat(
                            created_at.replace("Z", "+00:00")
                        )
                    else:
                        created_date = created_at

                    age_days = (
                        datetime.now().replace(tzinfo=created_date.tzinfo)
                        - created_date
                    ).days

                    if age_days <= 30:
                        facets["age_range"]["recent (< 1 month)"] += 1
                    elif age_days <= 90:
                        facets["age_range"]["fresh (1-3 months)"] += 1
                    elif age_days <= 365:
                        facets["age_range"]["mature (3-12 months)"] += 1
                    else:
                        facets["age_range"]["established (> 1 year)"] += 1
                except (ValueError, TypeError):
                    facets["age_range"]["unknown"] += 1

            # Language facets
            language = metadata.get("language", metadata.get("programming_language"))
            if language:
                facets["language"][language.lower()] += 1

            # Framework facets
            framework = metadata.get("framework")
            if framework:
                if isinstance(framework, list):
                    for fw in framework:
                        facets["framework"][fw.lower()] += 1
                else:
                    facets["framework"][framework.lower()] += 1

            # Source facets
            source = metadata.get("source", metadata.get("origin", "unknown"))
            facets["source"][source] += 1

        # Convert defaultdicts to regular dicts and sort by count
        result = {}
        for facet_name, facet_values in facets.items():
            if facet_values:
                result[facet_name] = dict(
                    sorted(facet_values.items(), key=lambda x: x[1], reverse=True)
                )

        return result

    def apply_facet_filters(
        self, documents: list[dict[str, Any]], filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Apply facet filters to a list of documents.

        Args:
            documents: List of documents to filter
            filters: Dictionary of filters to apply

        Returns:
            Filtered list of documents
        """
        if not filters:
            return documents

        filtered_docs = []

        for doc in documents:
            metadata = doc.get("metadata", {})
            include_doc = True

            # Technology stack filter
            if "technology_stack" in filters:
                required_techs = filters["technology_stack"]
                if isinstance(required_techs, str):
                    required_techs = [required_techs]

                doc_techs = metadata.get("technology_stack", [])
                if isinstance(doc_techs, str):
                    doc_techs = [doc_techs]

                doc_techs_lower = [tech.lower() for tech in doc_techs]
                if not any(tech.lower() in doc_techs_lower for tech in required_techs):
                    include_doc = False

            # Complexity filter
            if include_doc and "complexity" in filters:
                required_complexity = filters["complexity"]
                doc_complexity = metadata.get("complexity", "unknown")
                if isinstance(required_complexity, list):
                    if doc_complexity not in required_complexity:
                        include_doc = False
                else:
                    if doc_complexity != required_complexity:
                        include_doc = False

            # Pattern type filter
            if include_doc and "pattern_type" in filters:
                required_types = filters["pattern_type"]
                if isinstance(required_types, str):
                    required_types = [required_types]

                doc_type = metadata.get("pattern_type", metadata.get("type", "unknown"))
                if doc_type not in required_types:
                    include_doc = False

            # Success rate range filter
            if include_doc and "min_success_rate" in filters:
                min_rate = filters["min_success_rate"]
                doc_rate = metadata.get("success_rate", 0.0)
                if isinstance(doc_rate, (int, float)) and doc_rate < min_rate:
                    include_doc = False

            if include_doc:
                filtered_docs.append(doc)

        return filtered_docs
