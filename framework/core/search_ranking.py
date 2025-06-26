import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

class SearchRanker:
    """
    Ranks and fuses search results based on various criteria like similarity, recency,
    success rate, and contextual relevance.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self._logger = logging.getLogger(__name__)
        self.weights = {
            "similarity": 0.5,
            "recency": 0.2,
            "success_rate": 0.2,
            "context_match": 0.1,
            ** (weights if weights is not None else {})
        }
        # Normalize weights to ensure they sum to 1, if not already
        total_weight = sum(self.weights.values())
        if total_weight > 0:
            self.weights = {k: v / total_weight for k, v in self.weights.items()}
        else:
            self._logger.warning("No weights provided or sum to zero. Using default equal weights.")
            num_weights = len(self.weights)
            if num_weights > 0:
                self.weights = {k: 1.0 / num_weights for k in self.weights.keys()}
            else:
                self.weights = {"similarity": 1.0} # Fallback to similarity only

    def rank_and_fuse_results(
        self,
        results: List[Dict[str, Any]],
        query_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Ranks and fuses a list of search results.

        Args:
            results: A list of dictionaries, where each dictionary represents a search result.
                     Expected keys: 'session_id' (or 'id'), 'similarity_score', 'metadata',
                     and potentially 'final_status' (for sessions).
            query_context: A dictionary representing the current context of the query,
                           e.g., {"repository": "my-repo", "branch": "main", "error_type": "ImportError"}.

        Returns:
            A list of ranked results, each with an added 'final_score'.
        """
        if not results:
            return []

        ranked_results = []
        for result in results:
            final_score = 0.0
            similarity_score = result.get("similarity_score", 0.0)
            metadata = result.get("metadata", {})
            session_data = result.get("session_data", {}) # For results coming from KnowledgeManager

            # 1. Base Similarity Score
            final_score += similarity_score * self.weights.get("similarity", 0)

            # 2. Recency Boost
            timestamp_str = metadata.get("timestamp") or session_data.get("timestamp")
            if timestamp_str:
                try:
                    session_date = datetime.fromisoformat(timestamp_str)
                    days_old = (datetime.now() - session_date).days
                    # Decay recency boost over 30 days, max boost for very recent
                    recency_boost = max(0, 1 - (days_old / 30.0))
                    final_score += recency_boost * self.weights.get("recency", 0)
                except ValueError:
                    self._logger.warning(f"Invalid timestamp format: {timestamp_str}")

            # 3. Success Rate Boost (if applicable, primarily for session data)
            final_status = metadata.get("final_status") or session_data.get("final_status")
            if final_status == "success":
                final_score += 1.0 * self.weights.get("success_rate", 0)
            elif final_status == "partial_success":
                final_score += 0.5 * self.weights.get("success_rate", 0)

            # 4. Contextual Match Boost
            if query_context:
                context_match_score = self._calculate_context_match(metadata, query_context)
                final_score += context_match_score * self.weights.get("context_match", 0)

            result["final_score"] = final_score
            ranked_results.append(result)

        # Sort by final score in descending order
        ranked_results.sort(key=lambda x: x.get("final_score", 0.0), reverse=True)
        return ranked_results

    def _calculate_context_match(self, result_metadata: Dict[str, Any], query_context: Dict[str, Any]) -> float:
        """
        Calculates a score based on how well the result's metadata matches the query context.
        """
        match_score = 0.0
        matched_criteria = 0

        # Repository match
        if query_context.get("repository") and \
           query_context["repository"].lower() == result_metadata.get("repository", "").lower():
            match_score += 0.3
            matched_criteria += 1

        # Branch match
        if query_context.get("branch") and \
           query_context["branch"].lower() == result_metadata.get("branch", "").lower():
            match_score += 0.2
            matched_criteria += 1

        # Error type/category match (for error solutions)
        if query_context.get("error_category") and \
           query_context["error_category"].lower() == result_metadata.get("error_category", "").lower():
            match_score += 0.2
            matched_criteria += 1

        # Technology stack overlap (for code patterns)
        query_tech_stack = set(t.lower() for t in query_context.get("technology_stack", []))
        result_tech_stack = set(t.lower() for t in result_metadata.get("technology_stack", []))
        if query_tech_stack and result_tech_stack:
            overlap = len(query_tech_stack.intersection(result_tech_stack))
            if overlap > 0:
                match_score += 0.2 * (overlap / len(query_tech_stack))
                matched_criteria += 1

        # Normalize score by number of criteria considered, to avoid penalizing for missing context
        if matched_criteria > 0:
            return match_score / matched_criteria
        return 0.0
