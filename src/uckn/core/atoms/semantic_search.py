"""
UCKN Semantic Search Atom
"""

from typing import List, Optional, Dict
import logging

try:
    from ..semantic_search import SemanticSearchEngine
    SEMANTIC_SEARCH_ENGINE_AVAILABLE = True
except ImportError:
    logging.getLogger(__name__).warning(
        "SemanticSearchEngine not found. "
        "Semantic search capabilities will be limited."
    )
    SemanticSearchEngine = None
    SEMANTIC_SEARCH_ENGINE_AVAILABLE = False


class SemanticSearch:
    """
    Semantic search engine for knowledge patterns, wrapping SemanticSearchEngine.
    """

    def __init__(self, knowledge_dir: str = ".uckn/knowledge"):
        self._logger = logging.getLogger(__name__)
        if SEMANTIC_SEARCH_ENGINE_AVAILABLE:
            self.engine = SemanticSearchEngine(knowledge_dir=knowledge_dir)
        else:
            self.engine = None
            self._logger.warning("SemanticSearchEngine not available, semantic encoding/search will be disabled.")

    def is_available(self) -> bool:
        """Check if the underlying semantic search engine is available."""
        return self.engine is not None and self.engine.is_available()

    def encode(self, text: str) -> Optional[List[float]]:
        """
        Generate embeddings for text using the underlying sentence transformer model.
        """
        if not self.is_available():
            self._logger.warning("Semantic search engine not available, cannot encode text.")
            return None
        try:
            # The engine's generate_session_embedding expects a dict, but we just need encode
            # We can directly access the model if it's loaded.
            if self.engine.sentence_model:
                embedding = self.engine.sentence_model.encode(text, convert_to_numpy=True)
                return embedding.tolist()
            else:
                self._logger.error("Sentence transformer model not loaded in SemanticSearchEngine.")
                return None
        except Exception as e:
            self._logger.error(f"Failed to encode text: {e}")
            return None

    def search(self, query: str, collection_name: str, limit: int = 10, min_similarity: float = 0.7) -> List[Dict]:
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