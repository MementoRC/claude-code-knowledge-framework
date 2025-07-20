"""
UCKN Semantic Search Atom
"""

import logging
from typing import Any
from pathlib import Path

try:
    from ..semantic_search import SemanticSearchEngine
    SEMANTIC_SEARCH_ENGINE_AVAILABLE = True
    SearchEngineClass: type[Any] | None = SemanticSearchEngine
except ImportError:
    logging.getLogger(__name__).warning(
        "SemanticSearchEngine not found. "
        "Semantic search capabilities will be limited."
    )
    SEMANTIC_SEARCH_ENGINE_AVAILABLE = False
    SearchEngineClass = None


class SemanticSearch:
    """
    Semantic search engine for knowledge patterns, wrapping SemanticSearchEngine.
    """

    def __init__(self, knowledge_dir: str = ".uckn/knowledge"):
        from pathlib import Path
        self._logger = logging.getLogger(__name__)
        self.knowledge_dir = Path(knowledge_dir)
        self.engine: Any | None = None
        if SEMANTIC_SEARCH_ENGINE_AVAILABLE and SearchEngineClass:
            self.engine = SearchEngineClass(knowledge_dir=knowledge_dir)
        else:
            self._logger.warning("SemanticSearchEngine not available, semantic encoding/search will be disabled.")

    @property
    def embeddings_dir(self) -> Path:
        """Expose embeddings_dir from underlying engine."""
        if self.engine and hasattr(self.engine, 'embeddings_dir'):
            return self.engine.embeddings_dir
        return Path(self.knowledge_dir) / "embeddings"

    def is_available(self) -> bool:
        """Check if the underlying semantic search engine is available."""
        # Check if dependencies are available dynamically (for test patching)
        import uckn.core
        if hasattr(uckn.core, 'SENTENCE_TRANSFORMERS_AVAILABLE') and not uckn.core.SENTENCE_TRANSFORMERS_AVAILABLE:
            return False
        return self.engine is not None and self.engine.is_available()

    def encode(self, text: str) -> list[float] | None:
        """
        Generate embeddings for text using the underlying sentence transformer model.
        """
        if not self.is_available():
            self._logger.warning("Semantic search engine not available, cannot encode text.")
            return None
        try:
            # The engine's generate_session_embedding expects a dict, but we just need encode
            # We can directly access the model if it's loaded.
            if self.engine and hasattr(self.engine, 'sentence_model') and self.engine.sentence_model:
                embedding = self.engine.sentence_model.encode(text, convert_to_numpy=True)
                return embedding.tolist()
            else:
                self._logger.error("Sentence transformer model not loaded in SemanticSearchEngine.")
                return None
        except Exception as e:
            self._logger.error(f"Failed to encode text: {e}")
            return None

    def search(self, query: str, collection_name: str, limit: int = 10, min_similarity: float = 0.7) -> list[dict[str, Any]]:
        """
        Perform semantic search using the underlying engine's capabilities.
        Note: This method is primarily for direct semantic search on raw text.
        For searching stored patterns, KnowledgeManager's search_patterns should be used.
        """
        if not self.is_available():
            self._logger.warning("Semantic search engine not available, cannot perform search.")
            return []
        try:
            # SemanticSearchEngine.search_similar_sessions is designed for session data.
            # For general text search, we'd ideally use the ChromaDBConnector directly
            # with the query embedding.
            # This method might be redundant if KnowledgeManager handles all searches.
            # For now, let's make it delegate to the engine's search if possible,
            # or indicate it's not the primary search interface.
            self._logger.info(f"Performing semantic search for query: '{query}' in collection '{collection_name}'")
            # The SemanticSearchEngine's search_similar_sessions expects a query string
            # and searches its 'session_embeddings' collection.
            # To search other collections, we'd need direct ChromaDB access.
            # For now, let's assume this is a general text search that might not
            # directly map to specific ChromaDB collections managed by ChromaDBConnector.
            # If this `search` method is intended to search the *ChromaDBConnector's* collections,
            # it should take a ChromaDBConnector instance.
            # Given the current structure, it's better for KnowledgeManager to orchestrate.
            self._logger.warning(
                "SemanticSearch.search is a placeholder. "
                "Use KnowledgeManager.search_patterns for searching stored knowledge."
            )
            return [] # This method is not directly used for stored patterns search by KM.
        except Exception as e:
            self._logger.error(f"Semantic search failed: {e}")
            return []

    def _extract_text_for_embedding(self, session_data: dict[str, Any]) -> str:
        """Extract meaningful text content from session data for embedding."""
        if not self.engine:
            self._logger.warning("Semantic search engine not available, cannot extract text.")
            return ""
        return self.engine._extract_text_for_embedding(session_data)

    def get_embedding_stats(self) -> dict[str, Any]:
        """Get statistics about stored embeddings."""
        if not self.engine:
            self._logger.warning("Semantic search engine not available, cannot get stats.")
            return {
                "total_embeddings": 0,
                "storage_type": "none",
                "model_available": False
            }
        return self.engine.get_embedding_stats()

    def search_similar_sessions(self, query: str, max_results: int = 10,
                              similarity_threshold: float = 0.7) -> list[dict[str, Any]]:
        """Search for similar sessions using semantic similarity."""
        if not self.engine:
            self._logger.warning("Semantic search engine not available, cannot search sessions.")
            return []
        return self.engine.search_similar_sessions(query, max_results, similarity_threshold)

    def store_session_embedding(self, session_id: str, session_data: dict[str, Any]) -> bool:
        """Store session embedding in vector database."""
        if not self.engine:
            self._logger.warning("Semantic search engine not available, cannot store embedding.")
            return False
        return self.engine.store_session_embedding(session_id, session_data)

    def _store_embedding_numpy(self, session_id: str, embedding: Any, session_data: dict[str, Any]) -> None:
        """Store embedding using numpy fallback."""
        if not self.engine:
            self._logger.warning("Semantic search engine not available, cannot store embedding.")
            return
        if hasattr(self.engine, '_store_embedding_numpy'):
            return self.engine._store_embedding_numpy(session_id, embedding, session_data)
        else:
            self._logger.warning("Numpy storage not available in underlying engine.")
