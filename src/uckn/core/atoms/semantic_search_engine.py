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
from typing import Any

from .multi_modal_embeddings import MultiModalEmbeddings

try:
    from ...storage.chromadb_connector import ChromaDBConnector
except ImportError:
    ChromaDBConnector = None


def _tech_stack_match(
    query_stack: list[str] | None, doc_stack: list[str] | None
) -> float:
    """
    Calculate compatibility score between two tech stacks.

    Args:
        query_stack: Technology stack from query
        doc_stack: Technology stack from document metadata

    Returns:
        Compatibility score between 0.0 and 1.0
    """
    if not query_stack or not doc_stack:
        return 0.0

    query_set = {stack.lower() for stack in query_stack}
    doc_set = {stack.lower() for stack in doc_stack}

    if not query_set or not doc_set:
        return 0.0

    intersection = query_set & doc_set
    union = query_set | doc_set

    return len(intersection) / len(union) if union else 0.0


class SemanticSearchEngine:
    """
    Core semantic search engine atom for code patterns and error solutions.

    Provides vector-based semantic search using multi-modal embeddings and ChromaDB,
    with support for technology stack filtering and advanced ranking algorithms.
    """

    def __init__(
        self,
        collection_name: str = "code_patterns",
        embedding_model: str = "sentence-transformers/all-mpnet-base-v2",
        **chromadb_kwargs: Any,
    ):
        """
        Initialize the semantic search engine.

        Args:
            collection_name: ChromaDB collection name
            embedding_model: Model name for sentence embeddings
            **chromadb_kwargs: Additional ChromaDB configuration
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self.collection_name = collection_name

        # Initialize ChromaDB connector
        if ChromaDBConnector:
            try:
                self.vector_store = ChromaDBConnector(**chromadb_kwargs)
                self._logger.info("ChromaDB connector initialized successfully")
            except Exception as e:
                self.vector_store = None
                self._logger.warning(f"ChromaDB connector initialization failed: {e}")
        else:
            self.vector_store = None
            self._logger.warning("ChromaDB not available")

        # Initialize multi-modal embeddings atom
        try:
            self.embeddings = MultiModalEmbeddings(model_name=embedding_model)
            self._logger.info("MultiModalEmbeddings initialized successfully")
        except Exception as e:
            self.embeddings = None
            self._logger.error(f"Failed to initialize MultiModalEmbeddings: {e}")

        # Simple instance cache for embeddings to avoid memory leaks from lru_cache
        self._embedding_cache: dict[tuple[str, str], list[float] | None] = {}

    def is_available(self) -> bool:
        """Check if the engine and its underlying components are available."""
        return bool(
            self.vector_store
            and self.vector_store.is_available()
            and self.embeddings
            and self.embeddings.is_available()
        )

    def store_pattern(
        self,
        pattern_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        content_type: str = "text",
    ) -> bool:
        """
        Store a code pattern or error solution in the vector database.

        Args:
            pattern_id: Unique identifier for the pattern
            content: Text content of the pattern
            metadata: Optional metadata dictionary
            content_type: Type of content (text, code, error)

        Returns:
            True if stored successfully, False otherwise
        """
        if not self.is_available():
            self._logger.warning("Search engine not available for storing patterns")
            return False

        try:
            # Generate embedding
            embedding = self._get_cached_embedding(content, content_type)
            if embedding is None:
                self._logger.warning(
                    f"Failed to generate embedding for pattern {pattern_id}"
                )
                return False

            # Store in vector database
            success = self.vector_store.add_documents(
                collection_name=self.collection_name,
                ids=[pattern_id],
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata] if metadata else None,
            )

            if success:
                self._logger.info(f"Pattern {pattern_id} stored successfully")
            else:
                self._logger.warning(f"Failed to store pattern {pattern_id}")

            return success

        except Exception as e:
            self._logger.error(f"Error storing pattern {pattern_id}: {e}")
            return False

    def search_similar(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.0,
        query_type: str = "text",
        tech_stack: list[str] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Search for similar patterns or solutions.

        Args:
            query: Search query text
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold
            query_type: Type of query (text, code, error, multi_modal)
            tech_stack: Technology stack for filtering
            **kwargs: Additional search parameters

        Returns:
            List of search results with scores and metadata
        """
        if not self.is_available():
            self._logger.warning("Search engine not available for searching")
            return []

        try:
            # Generate query embedding
            query_embedding = self._get_cached_embedding(query, query_type)
            if query_embedding is None:
                self._logger.warning("Failed to generate query embedding")
                return []

            # Perform vector search
            results = self.vector_store.query_collection(
                collection_name=self.collection_name,
                query_embeddings=[query_embedding],
                n_results=limit * 2,  # Get extra results for filtering
                **kwargs,
            )

            # Process and filter results
            processed_results = []
            for _, (doc_id, distance, doc_content, metadata) in enumerate(
                zip(
                    results.get("ids", [[]])[0],
                    results.get("distances", [[]])[0],
                    results.get("documents", [[]])[0],
                    results.get("metadatas", [{}])[0]
                    if results.get("metadatas")
                    else [{} for _ in range(len(results.get("ids", [[]])[0]))],
                    strict=False,
                )
            ):
                # Convert distance to similarity score (assuming cosine distance)
                similarity = 1.0 - distance

                if similarity < min_similarity:
                    continue

                result = {
                    "id": doc_id,
                    "content": doc_content,
                    "similarity": similarity,
                    "metadata": metadata or {},
                }

                # Tech stack filtering if specified
                if tech_stack:
                    doc_tech_stack = metadata.get("tech_stack", []) if metadata else []
                    compatibility = _tech_stack_match(tech_stack, doc_tech_stack)
                    if (
                        compatibility > 0.0
                    ):  # Only include if there's some compatibility
                        result["tech_compatibility"] = compatibility
                        processed_results.append(result)
                else:
                    processed_results.append(result)

                if len(processed_results) >= limit:
                    break

            self._logger.info(f"Found {len(processed_results)} similar patterns")
            return processed_results

        except Exception as e:
            self._logger.error(f"Error searching similar patterns: {e}")
            return []

    def search_by_tech_stack(
        self, tech_stack: list[str], limit: int = 10, min_compatibility: float = 0.3
    ) -> list[dict[str, Any]]:
        """
        Search patterns by technology stack compatibility.

        Args:
            tech_stack: List of technologies to match
            limit: Maximum number of results
            min_compatibility: Minimum tech stack compatibility score

        Returns:
            List of compatible patterns sorted by compatibility
        """
        if not self.is_available():
            self._logger.warning("Search engine not available")
            return []

        try:
            # Get all documents from collection
            results = self.vector_store.query_collection(
                collection_name=self.collection_name,
                query_embeddings=None,
                n_results=limit * 5,  # Get more for filtering
                include=["documents", "metadatas"],
            )

            # Filter and score by tech stack compatibility
            compatible_results = []
            for doc_id, doc_content, metadata in zip(
                results.get("ids", [[]])[0],
                results.get("documents", [[]])[0],
                results.get("metadatas", [{}])[0]
                if results.get("metadatas")
                else [{} for _ in range(len(results.get("ids", [[]])[0]))],
                strict=False,
            ):
                doc_tech_stack = metadata.get("tech_stack", []) if metadata else []
                compatibility = _tech_stack_match(tech_stack, doc_tech_stack)

                if compatibility >= min_compatibility:
                    compatible_results.append(
                        {
                            "id": doc_id,
                            "content": doc_content,
                            "metadata": metadata or {},
                            "tech_compatibility": compatibility,
                        }
                    )

            # Sort by compatibility score
            compatible_results.sort(key=lambda x: x["tech_compatibility"], reverse=True)
            return compatible_results[:limit]

        except Exception as e:
            self._logger.error(f"Error searching by tech stack: {e}")
            return []

    def multi_modal_search(
        self,
        query: str,
        tech_stack: list[str] | None = None,
        limit: int = 10,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Perform multi-modal search combining text and code embeddings.

        Args:
            query: Multi-modal search query
            tech_stack: Technology stack for filtering
            limit: Maximum number of results
            **kwargs: Additional search parameters

        Returns:
            Multi-modal search results
        """
        return self.search_similar(
            query=query,
            query_type="multi_modal",
            tech_stack=tech_stack,
            limit=limit,
            **kwargs,
        )

    def _get_cached_embedding(self, data: str, data_type: str) -> list[float] | None:
        """Get embedding with simple instance-level caching to avoid memory leaks."""
        cache_key = (data, data_type)

        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        # Generate new embedding
        embedding = None
        try:
            if data_type == "text":
                embedding = self.embeddings.embed_text(data)
            elif data_type == "code":
                embedding = self.embeddings.embed_code(data)
            elif data_type == "error":
                embedding = self.embeddings.embed_error(data)
            elif data_type == "multi_modal":
                embedding = self.embeddings.embed_multi_modal(data)
            else:
                self._logger.warning(f"Unknown data type: {data_type}")
                return None
        except Exception as e:
            self._logger.error(f"Error generating {data_type} embedding: {e}")
            return None

        # Cache the result (with basic size limit)
        if len(self._embedding_cache) > 1000:  # Simple cache eviction
            # Remove oldest 25% of entries
            items_to_remove = list(self._embedding_cache.keys())[:250]
            for key in items_to_remove:
                del self._embedding_cache[key]

        self._embedding_cache[cache_key] = embedding
        return embedding

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._embedding_cache.clear()
        self._logger.info("Embedding cache cleared")

    def get_collection_stats(self) -> dict[str, Any]:
        """
        Get statistics about the collection.

        Returns:
            Dictionary with collection statistics
        """
        if not self.is_available():
            return {"error": "Search engine not available"}

        try:
            stats = self.vector_store.get_collection_stats(self.collection_name)
            stats["cache_size"] = len(self._embedding_cache)
            return stats
        except Exception as e:
            self._logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}

    def delete_pattern(self, pattern_id: str) -> bool:
        """
        Delete a pattern from the collection.

        Args:
            pattern_id: ID of the pattern to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.is_available():
            self._logger.warning("Search engine not available")
            return False

        try:
            success = self.vector_store.delete_documents(
                collection_name=self.collection_name, ids=[pattern_id]
            )
            if success:
                self._logger.info(f"Pattern {pattern_id} deleted successfully")
            return success
        except Exception as e:
            self._logger.error(f"Error deleting pattern {pattern_id}: {e}")
            return False
