from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

# Defensive import to handle PyTorch docstring conflicts
_DISABLE_TORCH = os.environ.get("UCKN_DISABLE_TORCH", "0") == "1"

if _DISABLE_TORCH:
    logging.getLogger(__name__).warning(
        "Torch disabled by environment variable. "
        "Semantic encoding capabilities will be limited."
    )
    SentenceTransformer = None
    SENTENCE_TRANSFORMER_AVAILABLE = False
else:
    try:
        from sentence_transformers import SentenceTransformer

        SENTENCE_TRANSFORMER_AVAILABLE = True
    except (ImportError, RuntimeError) as e:
        logging.getLogger(__name__).warning(
            f"SentenceTransformer not available ({e}). "
            "Semantic encoding capabilities will be limited."
        )
        SentenceTransformer = None
        SENTENCE_TRANSFORMER_AVAILABLE = False

try:
    from .atoms.multi_modal_embeddings import MultiModalEmbeddings

    MULTI_MODAL_AVAILABLE = True
except ImportError:
    MultiModalEmbeddings = None
    MULTI_MODAL_AVAILABLE = False

try:
    from ..storage.chromadb_connector import ChromaDBConnector

    CHROMADB_AVAILABLE = True
except ImportError:
    ChromaDBConnector = None
    CHROMADB_AVAILABLE = False


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


class SemanticSearchEnhanced:
    """
    Enhanced semantic search engine with multi-modal support and optimizations.

    This class provides advanced semantic search capabilities combining text embeddings,
    code embeddings, and multi-modal search with ChromaDB integration. It supports
    various embedding models, caching, and technology stack filtering.
    """

    def __init__(
        self,
        sentence_model_name: str = "sentence-transformers/all-mpnet-base-v2",
        collection_name: str = "enhanced_code_patterns",
        **chromadb_kwargs: Any,
    ):
        """
        Initialize the enhanced semantic search engine.

        Args:
            sentence_model_name: Name of the sentence transformer model
            collection_name: ChromaDB collection name
            **chromadb_kwargs: Additional ChromaDB configuration
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self.collection_name = collection_name
        self._is_initialized = False

        # Initialize sentence transformer model
        self.sentence_model = None
        if SENTENCE_TRANSFORMER_AVAILABLE and SentenceTransformer:
            try:
                # Check if model exists locally first
                model_path = Path.home() / ".cache" / "huggingface" / "transformers"
                if model_path.exists():
                    self._logger.info(f"Loading cached model: {sentence_model_name}")

                self.sentence_model = SentenceTransformer(sentence_model_name)
                self._logger.info(
                    f"SentenceTransformer model loaded: {sentence_model_name}"
                )
            except Exception as e:
                self._logger.warning(f"Failed to load SentenceTransformer: {e}")
                self.sentence_model = None

        # Initialize multi-modal embeddings atom
        self.embedding_atom = None
        if MULTI_MODAL_AVAILABLE:
            try:
                self.embedding_atom = MultiModalEmbeddings(
                    model_name=sentence_model_name
                )
                self._logger.info("MultiModalEmbeddings atom initialized")
            except Exception as e:
                self.embedding_atom = None
                self._logger.warning(f"Failed to initialize MultiModalEmbeddings: {e}")

        # Initialize ChromaDB connector
        self.vector_store = None
        if CHROMADB_AVAILABLE:
            try:
                self.vector_store = ChromaDBConnector(**chromadb_kwargs)
                self._logger.info("ChromaDB connector initialized")
            except Exception as e:
                self.vector_store = None
                self._logger.warning(f"ChromaDB connector initialization failed: {e}")

        # Simple instance cache to avoid memory leaks from lru_cache
        self._encoding_cache: dict[str, list[float] | None] = {}
        self._embedding_cache: dict[tuple[str, str], list[float] | None] = {}

        # Mark as initialized if at least one component is available
        self._is_initialized = (
            self.sentence_model is not None or self.embedding_atom is not None
        ) and self.vector_store is not None

        if not self._is_initialized:
            self.embedding_atom = None
            self._logger.error("Failed to initialize SemanticSearchEnhanced components")

    def is_available(self) -> bool:
        """Check if the engine and its underlying components are fully available."""
        return self._is_initialized

    def encode(self, text: str) -> list[float] | None:
        """
        Generate embeddings for a single text using the underlying sentence transformer model.
        Results are cached using instance-level cache to avoid memory leaks.
        """
        if not self.is_available() or self.sentence_model is None:
            self._logger.warning(
                "SentenceTransformer model not available for text encoding"
            )
            return None

        # Check cache first
        if text in self._encoding_cache:
            return self._encoding_cache[text]

        try:
            # Generate embedding
            embedding = self.sentence_model.encode(text, convert_to_numpy=True)
            embedding_list = embedding.tolist()

            # Cache result (with basic size limit)
            if len(self._encoding_cache) > 1000:  # Simple cache eviction
                # Remove oldest 25% of entries
                items_to_remove = list(self._encoding_cache.keys())[:250]
                for key in items_to_remove:
                    del self._encoding_cache[key]

            self._encoding_cache[text] = embedding_list
            return embedding_list
        except Exception as e:
            self._logger.error(f"Error encoding text: {e}")
            return None

    def encode_batch(self, texts: list[str]) -> list[list[float]] | None:
        """
        Generate embeddings for multiple texts using batch processing.

        Args:
            texts: List of texts to encode

        Returns:
            List of embedding vectors or None if encoding fails
        """
        if not self.is_available() or self.sentence_model is None:
            self._logger.warning(
                "SentenceTransformer model not available for batch encoding"
            )
            return None

        try:
            # Check for cached results first
            cached_results = []
            uncached_texts = []
            uncached_indices = []

            for i, text in enumerate(texts):
                if text in self._encoding_cache:
                    cached_results.append((i, self._encoding_cache[text]))
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)

            # Process uncached texts
            if uncached_texts:
                embeddings = self.sentence_model.encode(
                    uncached_texts, convert_to_numpy=True
                )

                # Cache new results
                for text, embedding, idx in zip(
                    uncached_texts, embeddings, uncached_indices, strict=False
                ):
                    embedding_list = embedding.tolist()

                    # Simple cache management
                    if len(self._encoding_cache) > 1000:
                        items_to_remove = list(self._encoding_cache.keys())[:250]
                        for key in items_to_remove:
                            del self._encoding_cache[key]

                    self._encoding_cache[text] = embedding_list
                    cached_results.append((idx, embedding_list))

            # Sort results by original index
            cached_results.sort(key=lambda x: x[0])
            return [result[1] for result in cached_results]

        except Exception as e:
            self._logger.error(f"Error in batch encoding: {e}")
            return None

    def semantic_search(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.0,
        tech_stack: list[str] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Perform semantic search using sentence transformer embeddings.

        Args:
            query: Search query text
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold
            tech_stack: Technology stack for filtering
            **kwargs: Additional search parameters

        Returns:
            List of search results with scores and metadata
        """
        if not self.is_available():
            self._logger.warning("Semantic search engine not available")
            return []

        try:
            # Generate query embedding
            query_embedding = self.encode(query)
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
            for doc_id, distance, doc_content, metadata in zip(
                results.get("ids", [[]])[0],
                results.get("distances", [[]])[0],
                results.get("documents", [[]])[0],
                results.get("metadatas", [{}])[0]
                if results.get("metadatas")
                else [{} for _ in range(len(results.get("ids", [[]])[0]))],
                strict=False,
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

            return processed_results

        except Exception as e:
            self._logger.error(f"Error in semantic search: {e}")
            return []

    def multi_modal_search(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.0,
        tech_stack: list[str] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Perform multi-modal search using enhanced embeddings.

        Args:
            query: Multi-modal search query
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold
            tech_stack: Technology stack for filtering
            **kwargs: Additional search parameters

        Returns:
            List of multi-modal search results
        """
        if not self.is_available() or not self.embedding_atom:
            self._logger.warning("Multi-modal search not available")
            return self.semantic_search(
                query, limit, min_similarity, tech_stack, **kwargs
            )

        try:
            # Generate multi-modal query embedding
            query_embedding = self._get_cached_embedding(query, "multi_modal")
            if query_embedding is None:
                self._logger.warning("Failed to generate multi-modal query embedding")
                return []

            # Perform vector search
            results = self.vector_store.query_collection(
                collection_name=self.collection_name,
                query_embeddings=[query_embedding],
                n_results=limit * 2,  # Get extra results for filtering
                **kwargs,
            )

            # Process results with tech stack filtering
            processed_results = []
            for doc_id, distance, doc_content, metadata in zip(
                results.get("ids", [[]])[0],
                results.get("distances", [[]])[0],
                results.get("documents", [[]])[0],
                results.get("metadatas", [{}])[0]
                if results.get("metadatas")
                else [{} for _ in range(len(results.get("ids", [[]])[0]))],
                strict=False,
            ):
                similarity = 1.0 - distance

                if similarity < min_similarity:
                    continue

                result = {
                    "id": doc_id,
                    "content": doc_content,
                    "similarity": similarity,
                    "metadata": metadata or {},
                    "search_type": "multi_modal",
                }

                # Tech stack filtering
                if tech_stack:
                    doc_tech_stack = metadata.get("tech_stack", []) if metadata else []
                    compatibility = _tech_stack_match(tech_stack, doc_tech_stack)
                    if compatibility > 0.0:
                        result["tech_compatibility"] = compatibility
                        processed_results.append(result)
                else:
                    processed_results.append(result)

                if len(processed_results) >= limit:
                    break

            return processed_results

        except Exception as e:
            self._logger.error(f"Error in multi-modal search: {e}")
            return []

    def search_by_tech_stack_enhanced(
        self, tech_stack: list[str], limit: int = 10, min_compatibility: float = 0.3
    ) -> list[dict[str, Any]]:
        """
        Enhanced search by technology stack compatibility with better scoring.

        Args:
            tech_stack: List of technologies to match
            limit: Maximum number of results
            min_compatibility: Minimum tech stack compatibility score

        Returns:
            List of compatible patterns sorted by compatibility
        """
        if not self.is_available():
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
            filtered = []
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
                    result = {
                        "id": doc_id,
                        "content": doc_content,
                        "metadata": metadata or {},
                        "tech_compatibility": compatibility,
                    }
                    filtered.append(result)

            # Sort by compatibility score
            filtered.sort(key=lambda x: x["tech_compatibility"], reverse=True)
            return filtered[:limit]

        except Exception as e:
            self._logger.error(f"Error in enhanced tech stack search: {e}")
            return []

    def _get_cached_embedding(self, data: str, data_type: str) -> list[float] | None:
        """Get embedding with instance-level caching to avoid memory leaks."""
        cache_key = (data, data_type)

        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        # Generate new embedding
        embedding = None
        if self.embedding_atom:
            embedding = self.embedding_atom.embed(data, data_type=data_type)
        elif self.sentence_model and data_type == "text":
            # Fallback to SentenceTransformer for text
            try:
                embedding_array = self.sentence_model.encode(
                    data, convert_to_numpy=True
                )
                embedding = embedding_array.tolist()
            except Exception as e:
                self._logger.error(f"Error generating fallback embedding: {e}")
                return None
        else:
            self._logger.warning(
                f"No embedding method available for data_type: {data_type}"
            )
            return None

        # Cache the result (with basic size limit)
        if len(self._embedding_cache) > 1000:  # Simple cache eviction
            # Remove oldest 25% of entries
            items_to_remove = list(self._embedding_cache.keys())[:250]
            for key in items_to_remove:
                del self._embedding_cache[key]

        self._embedding_cache[cache_key] = embedding
        return embedding

    def store_enhanced_pattern(
        self,
        pattern_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        content_type: str = "text",
    ) -> bool:
        """
        Store a pattern with enhanced multi-modal embedding generation.

        Args:
            pattern_id: Unique identifier for the pattern
            content: Text content of the pattern
            metadata: Optional metadata dictionary
            content_type: Type of content for embedding generation

        Returns:
            True if stored successfully, False otherwise
        """
        if not self.is_available():
            return False

        try:
            # Generate appropriate embedding
            if self.embedding_atom and content_type != "text":
                embedding = self._get_cached_embedding(content, content_type)
            else:
                embedding = self.encode(content)

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

            return success

        except Exception as e:
            self._logger.error(f"Error storing enhanced pattern {pattern_id}: {e}")
            return False

    def clear_caches(self) -> None:
        """Clear all caches."""
        self._encoding_cache.clear()
        self._embedding_cache.clear()
        self._logger.info("All caches cleared")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "encoding_cache_size": len(self._encoding_cache),
            "embedding_cache_size": len(self._embedding_cache),
            "is_initialized": self._is_initialized,
            "has_sentence_model": self.sentence_model is not None,
            "has_embedding_atom": self.embedding_atom is not None,
            "has_vector_store": self.vector_store is not None,
        }
