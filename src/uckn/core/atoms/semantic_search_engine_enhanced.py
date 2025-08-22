"""
Enhanced Semantic Search Engine for UCKN

Environment-aware semantic search with automatic fallbacks:
- Production: Full ML models with sentence-transformers and ChromaDB
- Development: Partial ML capabilities with graceful degradation
- CI: Fast deterministic fallbacks for testing
- Disabled: Explicit disable mode
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from ..ml_environment_manager import get_ml_manager
from .multi_modal_embeddings import MultiModalEmbeddings
from ...storage.chromadb_connector import ChromaDBConnector


class EnhancedSemanticSearchEngine:
    """
    Environment-aware semantic search engine with automatic capability detection.

    Features:
    - Automatic ML environment detection
    - Graceful fallback to deterministic embeddings in CI
    - Real ML models in production environments
    - Performance optimization with caching
    - Async support for concurrent operations
    """

    def __init__(
        self,
        chroma_connector: Optional[ChromaDBConnector] = None,
        embedding_atom: Optional[MultiModalEmbeddings] = None,
        logger: Optional[logging.Logger] = None,
        cache_size: int = 256,
        enable_async: bool = True,
        enable_performance_mode: bool = True,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self._ml_manager = get_ml_manager()

        # Environment info logging
        env_info = self._ml_manager.get_environment_info()
        self.logger.info(
            f"Initializing semantic search - Environment: {env_info['environment']}"
        )

        self.enable_async = enable_async
        self.enable_performance_mode_flag = enable_performance_mode

        # Initialize ChromaDB connector
        self.chroma_connector = chroma_connector
        if self.chroma_connector is None and self._ml_manager.capabilities.chromadb:
            try:
                self.chroma_connector = ChromaDBConnector()
                if not self.chroma_connector.is_available():
                    self.logger.warning("ChromaDB connector created but not available")
                    self.chroma_connector = None
            except Exception as e:
                self.logger.warning(f"Failed to create ChromaDB connector: {e}")
                self.chroma_connector = None

        # Initialize embedding atom
        self.embedding_atom = embedding_atom or MultiModalEmbeddings()

        # Performance monitoring
        self._search_cache = {} if enable_performance_mode else None
        self._cache_size = cache_size
        self._performance_stats = {
            "searches_performed": 0,
            "cache_hits": 0,
            "avg_search_time": 0.0,
            "last_search_time": 0.0,
        }

    def is_available(self) -> bool:
        """Check if semantic search is available in current environment."""
        return self.embedding_atom.is_available()

    def get_capabilities(self) -> Dict[str, Any]:
        """Get detailed capabilities information."""
        env_info = self._ml_manager.get_environment_info()
        return {
            **env_info,
            "chroma_available": self.chroma_connector is not None
            and self.chroma_connector.is_available(),
            "embeddings_available": self.embedding_atom.is_available(),
            "search_available": self.is_available(),
            "performance_cache": self._search_cache is not None,
            "async_enabled": self.enable_async,
        }

    def _cache_key(
        self, query: Dict[str, Optional[str]], collection_name: str, **kwargs
    ) -> str:
        """Generate cache key for search query."""
        query_str = str(sorted(query.items()))
        params_str = str(sorted(kwargs.items()))
        return f"{collection_name}:{query_str}:{params_str}"

    def _get_cached_result(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached search result."""
        if not self._search_cache:
            return None
        return self._search_cache.get(cache_key)

    def _cache_result(self, cache_key: str, result: List[Dict[str, Any]]) -> None:
        """Cache search result."""
        if not self._search_cache:
            return

        # Implement LRU cache behavior
        if len(self._search_cache) >= self._cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self._search_cache))
            del self._search_cache[oldest_key]

        self._search_cache[cache_key] = result

    def _update_performance_stats(self, search_time: float, cache_hit: bool) -> None:
        """Update performance statistics."""
        self._performance_stats["searches_performed"] += 1
        self._performance_stats["last_search_time"] = search_time

        if cache_hit:
            self._performance_stats["cache_hits"] += 1
        else:
            # Update running average of actual search times (excluding cache hits)
            total_searches = (
                self._performance_stats["searches_performed"]
                - self._performance_stats["cache_hits"]
            )
            if total_searches == 1:
                self._performance_stats["avg_search_time"] = search_time
            else:
                # Running average update
                current_avg = self._performance_stats["avg_search_time"]
                self._performance_stats["avg_search_time"] = (
                    current_avg * (total_searches - 1) + search_time
                ) / total_searches

    def search(
        self,
        query: Dict[str, Optional[str]],
        collection_name: str,
        limit: int = 10,
        min_similarity: float = 0.7,
        metadata_filter: Optional[Dict[str, Any]] = None,
        combine_method: str = "mean",
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search with environment-aware capabilities.

        Args:
            query: Multi-modal query dict with 'code', 'text', 'config', 'error' keys
            collection_name: Target ChromaDB collection name
            limit: Maximum results to return
            min_similarity: Minimum similarity threshold
            metadata_filter: Optional metadata filtering
            combine_method: Method to combine multi-modal embeddings

        Returns:
            List of search results with similarity scores
        """
        start_time = time.time()

        # Check cache first
        cache_key = self._cache_key(
            query,
            collection_name,
            limit=limit,
            min_similarity=min_similarity,
            metadata_filter=metadata_filter,
            combine_method=combine_method,
        )

        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            search_time = time.time() - start_time
            self._update_performance_stats(search_time, cache_hit=True)
            self.logger.debug(f"Cache hit for query in {collection_name}")
            return cached_result

        # Perform actual search
        try:
            # Generate embedding for query
            query_embedding = self.embedding_atom.multi_modal_embed(
                code=query.get("code"),
                text=query.get("text"),
                config=query.get("config"),
                error=query.get("error"),
                combine_method=combine_method,
            )

            if query_embedding is None:
                self.logger.warning("Failed to generate embedding for query")
                return []

            # Search in ChromaDB if available
            if self.chroma_connector and self.chroma_connector.is_available():
                results = self.chroma_connector.search_documents(
                    collection_name=collection_name,
                    query_embedding=query_embedding,
                    n_results=limit,
                    min_similarity=min_similarity,
                    where_clause=metadata_filter,
                )
            else:
                # Fallback: return empty results with logging
                env_info = self._ml_manager.get_environment_info()
                self.logger.debug(
                    f"ChromaDB not available in {env_info['environment']} environment - "
                    "returning empty results"
                )
                results = []

            # Cache the result
            self._cache_result(cache_key, results)

            search_time = time.time() - start_time
            self._update_performance_stats(search_time, cache_hit=False)

            self.logger.debug(
                f"Search completed in {search_time:.3f}s - "
                f"Found {len(results)} results in {collection_name}"
            )

            return results

        except Exception as e:
            search_time = time.time() - start_time
            self.logger.error(f"Search failed after {search_time:.3f}s: {e}")
            return []

    async def search_async(
        self,
        query: Dict[str, Optional[str]],
        collection_name: str,
        limit: int = 10,
        min_similarity: float = 0.7,
        metadata_filter: Optional[Dict[str, Any]] = None,
        combine_method: str = "mean",
    ) -> List[Dict[str, Any]]:
        """Async version of search method."""
        if not self.enable_async:
            return self.search(
                query,
                collection_name,
                limit,
                min_similarity,
                metadata_filter,
                combine_method,
            )

        # Run search in thread pool to avoid blocking
        return await asyncio.to_thread(
            self.search,
            query,
            collection_name,
            limit,
            min_similarity,
            metadata_filter,
            combine_method,
        )

    def batch_search(
        self,
        queries: List[Dict[str, Optional[str]]],
        collection_name: str,
        limit: int = 10,
        min_similarity: float = 0.7,
        metadata_filter: Optional[Dict[str, Any]] = None,
        combine_method: str = "mean",
    ) -> List[List[Dict[str, Any]]]:
        """
        Perform batch search for multiple queries.

        Returns:
            List of search results for each query
        """
        start_time = time.time()

        # Generate embeddings in batch for efficiency
        embeddings = []
        for query in queries:
            embedding = self.embedding_atom.multi_modal_embed(
                code=query.get("code"),
                text=query.get("text"),
                config=query.get("config"),
                error=query.get("error"),
                combine_method=combine_method,
            )
            embeddings.append(embedding)

        # Perform searches
        results = []
        for i, (query, embedding) in enumerate(zip(queries, embeddings)):
            if embedding is None:
                self.logger.warning(f"Failed to generate embedding for query {i}")
                results.append([])
                continue

            if self.chroma_connector and self.chroma_connector.is_available():
                query_results = self.chroma_connector.search_documents(
                    collection_name=collection_name,
                    query_embedding=embedding,
                    n_results=limit,
                    min_similarity=min_similarity,
                    where_clause=metadata_filter,
                )
                results.append(query_results)
            else:
                results.append([])

        batch_time = time.time() - start_time
        self.logger.debug(
            f"Batch search completed in {batch_time:.3f}s - "
            f"Processed {len(queries)} queries"
        )

        return results

    async def batch_search_async(
        self,
        queries: List[Dict[str, Optional[str]]],
        collection_name: str,
        limit: int = 10,
        min_similarity: float = 0.7,
        metadata_filter: Optional[Dict[str, Any]] = None,
        combine_method: str = "mean",
    ) -> List[List[Dict[str, Any]]]:
        """Async version of batch search."""
        if not self.enable_async:
            return self.batch_search(
                queries,
                collection_name,
                limit,
                min_similarity,
                metadata_filter,
                combine_method,
            )

        return await asyncio.to_thread(
            self.batch_search,
            queries,
            collection_name,
            limit,
            min_similarity,
            metadata_filter,
            combine_method,
        )

    def add_document(
        self,
        collection_name: str,
        doc_id: str,
        document: str,
        metadata: Dict[str, Any],
        doc_type: str = "auto",
    ) -> bool:
        """
        Add document to semantic search index.

        Args:
            collection_name: Target collection
            doc_id: Unique document ID
            document: Document text content
            metadata: Document metadata
            doc_type: Document type for embedding ('code', 'text', 'config', 'error', 'auto')

        Returns:
            True if document was added successfully
        """
        try:
            # Generate embedding for document
            embedding = self.embedding_atom.embed(document, data_type=doc_type)
            if embedding is None:
                self.logger.error(f"Failed to generate embedding for document {doc_id}")
                return False

            # Store in ChromaDB if available
            if self.chroma_connector and self.chroma_connector.is_available():
                success = self.chroma_connector.add_document(
                    collection_name=collection_name,
                    doc_id=doc_id,
                    document=document,
                    embedding=embedding,
                    metadata=metadata,
                )
                if success:
                    self.logger.debug(f"Added document {doc_id} to {collection_name}")
                    # Clear cache since index has changed
                    if self._search_cache:
                        self._search_cache.clear()
                return success
            else:
                env_info = self._ml_manager.get_environment_info()
                self.logger.debug(
                    f"ChromaDB not available in {env_info['environment']} environment - "
                    "document not stored"
                )
                return False

        except Exception as e:
            self.logger.error(f"Failed to add document {doc_id}: {e}")
            return False

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        cache_hit_rate = 0.0
        if self._performance_stats["searches_performed"] > 0:
            cache_hit_rate = (
                self._performance_stats["cache_hits"]
                / self._performance_stats["searches_performed"]
            )

        return {
            **self._performance_stats,
            "cache_hit_rate": cache_hit_rate,
            "cache_size": len(self._search_cache) if self._search_cache else 0,
            "max_cache_size": self._cache_size,
            "environment": self._ml_manager.get_environment_info(),
        }

    def clear_cache(self) -> None:
        """Clear search cache."""
        if self._search_cache:
            self._search_cache.clear()
            self.logger.debug("Search cache cleared")

    def enable_performance_mode(self, enabled: bool = True) -> None:
        """Enable or disable performance optimizations."""
        if enabled:
            if self._search_cache is None:
                self._search_cache = {}
                self.logger.info("Performance mode enabled")
        else:
            if self._search_cache is not None:
                self._search_cache = None
                self.logger.info("Performance mode disabled")

        # Update the instance variable
        self.enable_performance_mode_flag = enabled
