"""
UCKN Semantic Search Engine Atom

Provides vector-based semantic search for code patterns and error solutions using
multi-modal embeddings and ChromaDB. Supports text, code, error, and multi-modal queries,
with technology stack filtering, LRU caching, and advanced ranking.

Integrates with:
- MultiModalEmbeddings atom for embedding generation
- ChromaDBConnector for vector search and storage

Author: UCKN Team
"""

import logging
from functools import lru_cache
from typing import Any

from .multi_modal_embeddings import MultiModalEmbeddings

try:
    from src.uckn.storage.chromadb_connector import ChromaDBConnector
except ImportError:
    ChromaDBConnector = None


def _tech_stack_match(
    query_stack: list[str] | None, doc_stack: list[str] | None
) -> float:
    """
    Compute a tech stack compatibility score between two stacks.
    Returns a float between 0.0 and 1.0.
    """
    if not query_stack or not doc_stack:
        return 0.5  # Neutral if unknown
    set_query = {s.lower() for s in query_stack}
    set_doc = {s.lower() for s in doc_stack}
    if not set_query or not set_doc:
        return 0.5
    intersection = set_query & set_doc
    union = set_query | set_doc
    if not union:
        return 0.5
    return len(intersection) / len(union)


class SemanticSearchEngine:
    """
    Vector-based semantic search engine for UCKN knowledge patterns and error solutions.

    Features:
    - Multi-modal query support (text, code, error, or combinations)
    - Uses MultiModalEmbeddings for embedding generation
    - Vector similarity search via ChromaDBConnector
    - Relevance ranking (similarity, success_rate, tech_stack_match)
    - Technology stack filtering
    - LRU caching for frequent queries
    - Supports all collection types (code_patterns, error_solutions)
    """

    def __init__(
        self,
        chroma_connector: Any | None = None,
        embedding_atom: MultiModalEmbeddings | None = None,
        logger: logging.Logger | None = None,
        cache_size: int = 128,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.chroma_connector = chroma_connector or (
            ChromaDBConnector() if ChromaDBConnector else None
        )
        self.embedding_atom = embedding_atom or MultiModalEmbeddings()
        self.cache_size = cache_size

        if not self.chroma_connector or not self.chroma_connector.is_available():
            self.logger.warning(
                "ChromaDBConnector not available. Semantic search will be disabled."
            )

        if not self.embedding_atom:
            self.logger.warning(
                "MultiModalEmbeddings atom not available. Embedding will be disabled."
            )

    def is_available(self) -> bool:
        """
        Checks if the component is initialized and ready for use.

        Returns:
            bool: True if component is ready, False otherwise.
        """
        # Check if dependencies and models are available
        return (
            self.chroma_connector is not None
            and self.chroma_connector.is_available()
            and self.embedding_atom is not None
            and self.embedding_atom.is_available()
        )

    def _get_collection(self, collection_type: str) -> str:
        if collection_type not in ("code_patterns", "error_solutions"):
            raise ValueError(f"Unknown collection type: {collection_type}")
        return collection_type

    def _get_success_rate(self, metadata: dict[str, Any]) -> float:
        # Try to extract a success rate from metadata, fallback to 0.5 if not present
        return float(
            metadata.get("success_rate", metadata.get("avg_resolution_time", 0.5))
        )

    def _extract_tech_stack(self, metadata: dict[str, Any]) -> list[str]:
        # Try to extract technology stack from metadata
        stack = metadata.get("technology_stack")
        if isinstance(stack, list):
            return stack
        elif isinstance(stack, str):
            return [stack]
        return []

    def _rank_results(
        self, results: list[dict[str, Any]], query_tech_stack: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """
        Rank results by a weighted combination of similarity, success_rate, and tech_stack_match.
        """
        ranked = []
        for r in results:
            sim = r.get("similarity_score", 0.0)
            meta = r.get("metadata", {})
            # Use success_rate if present, else avg_resolution_time (inverted)
            if "success_rate" in meta:
                success = float(meta.get("success_rate", 0.5))
            elif "avg_resolution_time" in meta:
                # Lower time is better, so invert and normalize (assume max 1000 for safety)
                t = float(meta.get("avg_resolution_time", 1000.0))
                success = max(0.0, 1.0 - min(t, 1000.0) / 1000.0)
            else:
                success = 0.5
            doc_stack = self._extract_tech_stack(meta)
            tech_score = _tech_stack_match(query_tech_stack, doc_stack)
            # Weighted sum: similarity (0.6), success (0.2), tech_stack (0.2)
            rank_score = 0.6 * sim + 0.2 * success + 0.2 * tech_score
            r["_rank_score"] = rank_score
            r["_tech_stack_score"] = tech_score
            r["_success_score"] = success
            ranked.append(r)
        ranked.sort(key=lambda x: x["_rank_score"], reverse=True)
        return ranked

    def _filter_by_tech_stack(
        self, results: list[dict[str, Any]], query_tech_stack: list[str] | None
    ) -> list[dict[str, Any]]:
        """
        Optionally filter results by technology stack compatibility.
        """
        if not query_tech_stack:
            return results
        filtered = []
        for r in results:
            doc_stack = self._extract_tech_stack(r.get("metadata", {}))
            if _tech_stack_match(query_tech_stack, doc_stack) > 0.0:
                filtered.append(r)
        return filtered

    @lru_cache(maxsize=128)
    def _cached_embed(self, data: str, data_type: str) -> list[float] | None:
        # Use MultiModalEmbeddings for embedding
        return self.embedding_atom.embed(data, data_type=data_type)

    def _embed_query(self, text=None, code=None, error=None) -> list[float] | None:
        # Use multi-modal embedding if more than one modality is present
        if sum(x is not None for x in [text, code, error]) > 1:
            return self.embedding_atom.multi_modal_embed(
                text=text, code=code, error=error
            )
        elif code is not None:
            return self._cached_embed(code, "code")
        elif error is not None:
            return self._cached_embed(error, "error")
        elif text is not None:
            return self._cached_embed(text, "text")
        else:
            return None

    def _search_collection(
        self,
        query_embedding: list[float],
        collection_type: str,
        limit: int,
        min_similarity: float,
        tech_stack: list[str] | None = None,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Perform vector search in the specified collection.
        """
        if not self.chroma_connector or not self.chroma_connector.is_available():
            self.logger.warning("ChromaDBConnector not available, cannot search.")
            return []
        try:
            results = self.chroma_connector.search_documents(
                collection_name=self._get_collection(collection_type),
                query_embedding=query_embedding,
                n_results=limit * 2,  # Overfetch for better ranking/filtering
                min_similarity=min_similarity,
                where_clause=metadata_filter,
            )
        except Exception as e:
            self.logger.error(f"ChromaDB search failed: {e}")
            return []
        # Optionally filter by tech stack
        results = self._filter_by_tech_stack(results, tech_stack)
        return results[:limit]

    def _parse_tech_stack(self, tech_stack) -> list[str] | None:
        if tech_stack is None:
            return None
        if isinstance(tech_stack, str):
            return [tech_stack]
        if isinstance(tech_stack, list):
            return tech_stack
        return None

    # --- Public API ---

    def search_by_text(
        self, query_text: str, tech_stack=None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Semantic search for code patterns and error solutions by text.

        Args:
            query_text: Natural language query.
            tech_stack: Optional technology stack filter (str or list).
            limit: Max results.

        Returns:
            Ranked list of matching documents.
        """
        query_tech_stack = self._parse_tech_stack(tech_stack)
        embedding = self._cached_embed(query_text, "text")
        if embedding is None:
            self.logger.warning("Failed to generate embedding for text query.")
            return []
        results = []
        for collection in ("code_patterns", "error_solutions"):
            res = self._search_collection(
                query_embedding=embedding,
                collection_type=collection,
                limit=limit,
                min_similarity=0.7,
                tech_stack=query_tech_stack,
            )
            results.extend(res)
        ranked = self._rank_results(results, query_tech_stack)
        return ranked[:limit]

    def search_by_code(
        self, code_snippet: str, tech_stack=None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Semantic search for code patterns and error solutions by code snippet.

        Args:
            code_snippet: Code string.
            tech_stack: Optional technology stack filter (str or list).
            limit: Max results.

        Returns:
            Ranked list of matching documents.
        """
        query_tech_stack = self._parse_tech_stack(tech_stack)
        embedding = self._cached_embed(code_snippet, "code")
        if embedding is None:
            self.logger.warning("Failed to generate embedding for code query.")
            return []
        results = []
        for collection in ("code_patterns", "error_solutions"):
            res = self._search_collection(
                query_embedding=embedding,
                collection_type=collection,
                limit=limit,
                min_similarity=0.7,
                tech_stack=query_tech_stack,
            )
            results.extend(res)
        ranked = self._rank_results(results, query_tech_stack)
        return ranked[:limit]

    def search_by_error(
        self, error_message: str, tech_stack=None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Semantic search for error solutions and code patterns by error message.

        Args:
            error_message: Error message string.
            tech_stack: Optional technology stack filter (str or list).
            limit: Max results.

        Returns:
            Ranked list of matching documents.
        """
        query_tech_stack = self._parse_tech_stack(tech_stack)
        embedding = self._cached_embed(error_message, "error")
        if embedding is None:
            self.logger.warning("Failed to generate embedding for error query.")
            return []
        results = []
        for collection in ("error_solutions", "code_patterns"):
            res = self._search_collection(
                query_embedding=embedding,
                collection_type=collection,
                limit=limit,
                min_similarity=0.7,
                tech_stack=query_tech_stack,
            )
            results.extend(res)
        ranked = self._rank_results(results, query_tech_stack)
        return ranked[:limit]

    def search_multi_modal(
        self,
        text: str | None = None,
        code: str | None = None,
        error: str | None = None,
        tech_stack=None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Multi-modal semantic search using any combination of text, code, and error.

        Args:
            text: Optional text query.
            code: Optional code snippet.
            error: Optional error message.
            tech_stack: Optional technology stack filter (str or list).
            limit: Max results.

        Returns:
            Ranked list of matching documents.
        """
        query_tech_stack = self._parse_tech_stack(tech_stack)
        embedding = self._embed_query(text=text, code=code, error=error)
        if embedding is None:
            self.logger.warning("Failed to generate embedding for multi-modal query.")
            return []
        results = []
        for collection in ("code_patterns", "error_solutions"):
            res = self._search_collection(
                query_embedding=embedding,
                collection_type=collection,
                limit=limit,
                min_similarity=0.7,
                tech_stack=query_tech_stack,
            )
            results.extend(res)
        ranked = self._rank_results(results, query_tech_stack)
        return ranked[:limit]
