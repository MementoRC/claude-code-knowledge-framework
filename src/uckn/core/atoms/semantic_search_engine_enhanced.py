"""Enhanced semantic search engine with advanced features."""

import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from .multi_modal_embeddings import MultiModalEmbeddings

try:
    from ...storage.chromadb_connector import ChromaDBConnector
except ImportError:
    ChromaDBConnector = None


class VectorDBConnector:
    """Simple wrapper around ChromaDB connector for compatibility."""

    def __init__(self):
        """Initialize the connector."""
        self.chroma_connector = ChromaDBConnector() if ChromaDBConnector else None

    def similarity_search(
        self, embedding: List[float], limit: int, filters=None, include_metadata=True
    ):
        """Perform similarity search."""
        if self.chroma_connector:
            # Basic similarity search - would need to implement properly
            return []
        return []

    def keyword_search(
        self, query: str, limit: int, filters=None, include_metadata=True
    ):
        """Perform keyword search."""
        # Placeholder implementation
        return []


class EnhancedEmbeddingEngine:
    """Enhanced embedding engine wrapper around MultiModalEmbeddings."""

    def __init__(self):
        """Initialize the embedding engine."""
        self.embeddings = MultiModalEmbeddings()

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text."""
        try:
            embedding = self.embeddings.embed(text, data_type="text")
            if embedding is not None and len(embedding) > 0:
                return (
                    embedding.tolist()
                    if hasattr(embedding, "tolist")
                    else list(embedding)
                )
            return None
        except Exception:
            return None


class SemanticSearchEngineEnhanced:
    """Enhanced semantic search engine with advanced features."""

    def __init__(
        self,
        db_connector: Optional[VectorDBConnector] = None,
        embedding_engine: Optional[EnhancedEmbeddingEngine] = None,
    ):
        """
        Initialize enhanced semantic search engine.

        Args:
            db_connector: Vector database connector
            embedding_engine: Enhanced embedding engine
        """
        self.logger = logging.getLogger(__name__)
        self.db_connector = db_connector or VectorDBConnector()
        self.embedding_engine = embedding_engine or EnhancedEmbeddingEngine()

        # Advanced features
        self.search_cache = {}
        self.cache_lock = threading.Lock()
        self.max_cache_size = 1000
        self.search_analytics = {}

        # Context-aware search settings
        self.context_weights = {"semantic": 0.6, "keyword": 0.3, "temporal": 0.1}

        # Multi-modal search capabilities
        self.modality_weights = {"text": 0.7, "image": 0.2, "audio": 0.1}

    def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
        search_mode: str = "hybrid",
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform enhanced semantic search.

        Args:
            query: Search query
            limit: Maximum number of results
            filters: Search filters
            include_metadata: Whether to include metadata
            search_mode: Search mode (semantic, keyword, hybrid)
            context: Additional context for search

        Returns:
            List of search results
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_engine.generate_embedding(query)
            if query_embedding is None:
                self.logger.warning("Failed to generate embedding for query")
                return []

            # Apply search mode
            if search_mode == "semantic":
                results = self._semantic_search(
                    query_embedding, limit, filters, include_metadata
                )
            elif search_mode == "keyword":
                results = self._keyword_search(query, limit, filters, include_metadata)
            else:  # hybrid
                results = self._hybrid_search(
                    query, query_embedding, limit, filters, include_metadata
                )

            # Apply context-aware ranking if context provided
            if context:
                results = self._apply_context_ranking(results, context)

            # Update search analytics
            self._update_search_analytics(query, search_mode, len(results))

            return results

        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            return []

    def multi_query_search(
        self,
        queries: List[str],
        limit: int = 10,
        aggregate_method: str = "union",
        weights: Optional[List[float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform search across multiple queries.

        Args:
            queries: List of search queries
            limit: Maximum results per query
            aggregate_method: How to aggregate results (union, intersection, weighted)
            weights: Query weights for weighted aggregation

        Returns:
            Aggregated search results
        """
        if not queries:
            return []

        try:
            # Generate embeddings for all queries
            embeddings = []
            for i, query in enumerate(queries):
                embedding = self.embedding_engine.generate_embedding(query)
                if embedding is None:
                    self.logger.warning(f"Failed to generate embedding for query {i}")
                embeddings.append(embedding)

            # Perform searches
            results = []
            for i, (_query, embedding) in enumerate(
                zip(queries, embeddings, strict=False)
            ):
                if embedding is None:
                    self.logger.warning(f"Failed to generate embedding for query {i}")
                    results.append([])
                    continue

                query_results = self._semantic_search(embedding, limit)
                results.append(query_results)

            # Aggregate results
            return self._aggregate_results(results, aggregate_method, weights)

        except Exception as e:
            self.logger.error(f"Multi-query search failed: {str(e)}")
            return []

    def similarity_search(
        self,
        document: str,
        limit: int = 10,
        threshold: float = 0.7,
        exclude_self: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Find documents similar to given document.

        Args:
            document: Input document
            limit: Maximum number of results
            threshold: Similarity threshold
            exclude_self: Exclude the input document from results

        Returns:
            List of similar documents
        """
        try:
            # Generate document embedding
            doc_embedding = self.embedding_engine.generate_embedding(document)
            if doc_embedding is None:
                self.logger.warning("Failed to generate embedding for document")
                return []

            # Perform similarity search
            results = self.db_connector.similarity_search(
                doc_embedding, limit * 2 if exclude_self else limit
            )

            # Filter by threshold
            filtered_results = [
                result for result in results if result.get("similarity", 0) >= threshold
            ]

            # Exclude self if requested
            if exclude_self:
                filtered_results = [
                    result
                    for result in filtered_results
                    if result.get("content", "") != document
                ]

            return filtered_results[:limit]

        except Exception as e:
            self.logger.error(f"Similarity search failed: {str(e)}")
            return []

    def contextual_search(
        self,
        query: str,
        context: Dict[str, Any],
        limit: int = 10,
        context_boost: float = 0.2,
    ) -> List[Dict[str, Any]]:
        """
        Perform context-aware search.

        Args:
            query: Search query
            context: Contextual information
            limit: Maximum number of results
            context_boost: Context relevance boost factor

        Returns:
            Context-aware search results
        """
        try:
            # Get base search results
            base_results = self.search(query, limit * 2, context=context)

            # Apply context-specific boosting
            boosted_results = []
            for result in base_results:
                boost_score = self._calculate_context_boost(result, context)
                result["context_boost"] = boost_score
                result["boosted_score"] = result.get("similarity", 0) + (
                    boost_score * context_boost
                )
                boosted_results.append(result)

            # Sort by boosted score and return top results
            boosted_results.sort(key=lambda x: x["boosted_score"], reverse=True)
            return boosted_results[:limit]

        except Exception as e:
            self.logger.error(f"Contextual search failed: {str(e)}")
            return []

    def _semantic_search(
        self,
        query_embedding: List[float],
        limit: int,
        filters: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
    ) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings."""
        try:
            return self.db_connector.similarity_search(
                query_embedding, limit, filters, include_metadata
            )
        except Exception as e:
            self.logger.error(f"Semantic search failed: {str(e)}")
            return []

    def _keyword_search(
        self,
        query: str,
        limit: int,
        filters: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
    ) -> List[Dict[str, Any]]:
        """Perform keyword-based search."""
        try:
            # Simple keyword matching (could be enhanced with full-text search)
            return self.db_connector.keyword_search(
                query, limit, filters, include_metadata
            )
        except Exception as e:
            self.logger.error(f"Keyword search failed: {str(e)}")
            return []

    def _hybrid_search(
        self,
        query: str,
        query_embedding: List[float],
        limit: int,
        filters: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining semantic and keyword methods."""
        try:
            # Get semantic results
            semantic_results = self._semantic_search(
                query_embedding, limit, filters, include_metadata
            )

            # Get keyword results
            keyword_results = self._keyword_search(
                query, limit, filters, include_metadata
            )

            # Merge and deduplicate results
            merged_results = self._merge_search_results(
                semantic_results, keyword_results, limit
            )

            return merged_results

        except Exception as e:
            self.logger.error(f"Hybrid search failed: {str(e)}")
            return []

    def _merge_search_results(
        self,
        semantic_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Merge semantic and keyword search results."""
        try:
            # Create a dict to avoid duplicates (by content hash or id)
            merged_dict = {}

            # Add semantic results with boosted scores
            for result in semantic_results:
                key = result.get("id", result.get("content", ""))[:100]
                result["search_type"] = "semantic"
                result["combined_score"] = (
                    result.get("similarity", 0) * self.context_weights["semantic"]
                )
                merged_dict[key] = result

            # Add keyword results, boost if already exists
            for result in keyword_results:
                key = result.get("id", result.get("content", ""))[:100]
                keyword_score = (
                    result.get("score", 0.5) * self.context_weights["keyword"]
                )

                if key in merged_dict:
                    # Boost existing result
                    merged_dict[key]["combined_score"] += keyword_score
                    merged_dict[key]["search_type"] = "hybrid"
                else:
                    # Add new keyword result
                    result["search_type"] = "keyword"
                    result["combined_score"] = keyword_score
                    merged_dict[key] = result

            # Sort by combined score and return top results
            sorted_results = sorted(
                merged_dict.values(), key=lambda x: x["combined_score"], reverse=True
            )

            return sorted_results[:limit]

        except Exception as e:
            self.logger.error(f"Failed to merge search results: {str(e)}")
            return semantic_results[:limit]  # Fallback to semantic only

    def _apply_context_ranking(
        self,
        results: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Apply context-aware ranking to search results."""
        try:
            for result in results:
                context_score = self._calculate_context_score(result, context)
                original_score = result.get(
                    "combined_score", result.get("similarity", 0)
                )
                result["context_score"] = context_score
                result["final_score"] = original_score + context_score

            # Re-sort by final score
            results.sort(key=lambda x: x["final_score"], reverse=True)
            return results

        except Exception as e:
            self.logger.error(f"Context ranking failed: {str(e)}")
            return results

    def _calculate_context_score(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any],
    ) -> float:
        """Calculate context relevance score for a result."""
        try:
            context_score = 0.0

            # Temporal context
            if "timestamp" in context and "timestamp" in result:
                time_diff = abs(
                    datetime.fromisoformat(context["timestamp"]).timestamp()
                    - datetime.fromisoformat(result["timestamp"]).timestamp()
                )
                # Boost recent documents (within 24 hours)
                if time_diff < 86400:  # 24 hours in seconds
                    context_score += 0.1

            # Domain/category context
            if "domain" in context and "domain" in result:
                if context["domain"] == result["domain"]:
                    context_score += 0.2

            # User context
            if "user_id" in context and "author" in result:
                if context["user_id"] == result["author"]:
                    context_score += 0.15

            return context_score

        except Exception as e:
            self.logger.error(f"Context score calculation failed: {str(e)}")
            return 0.0

    def _calculate_context_boost(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any],
    ) -> float:
        """Calculate context boost score for a result."""
        return self._calculate_context_score(result, context)

    def _aggregate_results(
        self,
        results: List[List[Dict[str, Any]]],
        method: str,
        weights: Optional[List[float]] = None,
    ) -> List[Dict[str, Any]]:
        """Aggregate results from multiple queries."""
        try:
            if not results:
                return []

            if method == "union":
                # Simple union - combine all results and deduplicate
                all_results = []
                for result_set in results:
                    all_results.extend(result_set)

                # Deduplicate by content/id
                seen = set()
                unique_results = []
                for result in all_results:
                    key = result.get("id", result.get("content", ""))[:100]
                    if key not in seen:
                        seen.add(key)
                        unique_results.append(result)

                return unique_results

            elif method == "weighted" and weights:
                # Weighted aggregation
                weighted_results = {}
                for i, result_set in enumerate(results):
                    weight = weights[i] if i < len(weights) else 1.0
                    for result in result_set:
                        key = result.get("id", result.get("content", ""))[:100]
                        if key in weighted_results:
                            weighted_results[key]["combined_score"] += (
                                result.get("similarity", 0) * weight
                            )
                        else:
                            result["combined_score"] = (
                                result.get("similarity", 0) * weight
                            )
                            weighted_results[key] = result

                return sorted(
                    weighted_results.values(),
                    key=lambda x: x["combined_score"],
                    reverse=True,
                )

            else:
                # Default to first result set
                return results[0] if results else []

        except Exception as e:
            self.logger.error(f"Result aggregation failed: {str(e)}")
            return results[0] if results else []

    def _update_search_analytics(self, query: str, search_mode: str, result_count: int):
        """Update search analytics."""
        try:
            timestamp = datetime.now().isoformat()
            self.search_analytics[timestamp] = {
                "query": query,
                "mode": search_mode,
                "result_count": result_count,
                "timestamp": timestamp,
            }

            # Keep only last 1000 entries
            if len(self.search_analytics) > 1000:
                oldest_keys = sorted(self.search_analytics.keys())[:100]
                for key in oldest_keys:
                    del self.search_analytics[key]

        except Exception as e:
            self.logger.error(f"Analytics update failed: {str(e)}")

    def get_search_analytics(self) -> Dict[str, Any]:
        """Get search analytics summary."""
        try:
            if not self.search_analytics:
                return {}

            total_searches = len(self.search_analytics)
            mode_counts = {}
            avg_results = 0

            for analytics in self.search_analytics.values():
                mode = analytics.get("mode", "unknown")
                mode_counts[mode] = mode_counts.get(mode, 0) + 1
                avg_results += analytics.get("result_count", 0)

            avg_results = avg_results / total_searches if total_searches > 0 else 0

            return {
                "total_searches": total_searches,
                "mode_distribution": mode_counts,
                "average_results": avg_results,
                "analytics_period": {
                    "start": min(self.search_analytics.keys())
                    if self.search_analytics
                    else None,
                    "end": max(self.search_analytics.keys())
                    if self.search_analytics
                    else None,
                },
            }

        except Exception as e:
            self.logger.error(f"Analytics summary failed: {str(e)}")
            return {}

    def clear_cache(self):
        """Clear search cache."""
        with self.cache_lock:
            self.search_cache.clear()

    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information."""
        with self.cache_lock:
            return {
                "cache_size": len(self.search_cache),
                "max_cache_size": self.max_cache_size,
            }
