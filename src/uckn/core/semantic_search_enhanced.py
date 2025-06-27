import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from functools import lru_cache

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMER_AVAILABLE = True
except ImportError:
    logging.getLogger(__name__).warning(
        "SentenceTransformer not found. "
        "Semantic encoding capabilities will be limited."
    )
    SentenceTransformer = None
    SENTENCE_TRANSFORMER_AVAILABLE = False

try:
    from src.uckn.storage.chromadb_connector import ChromaDBConnector
    CHROMADB_CONNECTOR_AVAILABLE = True
except ImportError:
    logging.getLogger(__name__).warning(
        "ChromaDBConnector not found. "
        "ChromaDB integration for semantic search will be disabled."
    )
    ChromaDBConnector = None
    CHROMADB_CONNECTOR_AVAILABLE = False

class EnhancedSemanticSearchEngine:
    """
    Enhanced semantic search engine using sentence transformers and ChromaDB.

    Provides embedding-based similarity search for knowledge management with
    features like LRU caching, batch processing, and robust error handling.
    """

    def __init__(self, knowledge_dir: str = ".uckn/knowledge",
                 model_name: str = "all-MiniLM-L6-v2",
                 device: str = "cpu"):
        self._logger = logging.getLogger(__name__)
        self.knowledge_dir = knowledge_dir
        self.model_name = model_name
        self.device = device
        self.sentence_model: Optional[SentenceTransformer] = None
        self.chroma_connector: Optional[ChromaDBConnector] = None
        self._is_initialized = False

        self._initialize_components()

    def _initialize_components(self) -> None:
        """Initializes the sentence transformer model and ChromaDB connector."""
        try:
            if SENTENCE_TRANSFORMER_AVAILABLE:
                self._init_sentence_transformer()
            else:
                self._logger.warning("SentenceTransformer not available, semantic encoding will be disabled.")

            if CHROMADB_CONNECTOR_AVAILABLE:
                self._init_chromadb()
            else:
                self._logger.warning("ChromaDBConnector not available, ChromaDB search will be disabled.")

            if self.sentence_model and self.chroma_connector and self.chroma_connector.is_available():
                self._is_initialized = True
                self._logger.info("EnhancedSemanticSearchEngine initialized successfully.")
            else:
                self._is_initialized = False
                self._logger.warning("EnhancedSemanticSearchEngine could not be fully initialized due to missing dependencies or connection issues.")

        except Exception as e:
            self._logger.error(f"Failed to initialize EnhancedSemanticSearchEngine: {e}")
            self._is_initialized = False

    def _init_sentence_transformer(self) -> None:
        """Loads the sentence transformer model."""
        try:
            self.sentence_model = SentenceTransformer(self.model_name, device=self.device)
            self._logger.info(f"SentenceTransformer model '{self.model_name}' loaded on device '{self.device}'.")
        except Exception as e:
            self.sentence_model = None
            self._logger.error(f"Failed to load SentenceTransformer model '{self.model_name}': {e}")

    def _init_chromadb(self) -> None:
        """Initializes the ChromaDBConnector."""
        try:
            db_path = Path(self.knowledge_dir) / "chroma_db"
            self.chroma_connector = ChromaDBConnector(db_path=str(db_path))
            if not self.chroma_connector.is_available():
                self._logger.error("ChromaDBConnector initialized but not available.")
                self.chroma_connector = None
            else:
                self._logger.info(f"ChromaDBConnector initialized at {db_path}.")
        except Exception as e:
            self.chroma_connector = None
            self._logger.error(f"Failed to initialize ChromaDBConnector: {e}")

    def is_available(self) -> bool:
        """Check if the engine and its underlying components are fully available."""
        return self._is_initialized

    @lru_cache(maxsize=128) # Cache for single text encodings
    def encode(self, text: str) -> Optional[List[float]]:
        """
        Generate embeddings for a single text using the underlying sentence transformer model.
        Results are cached using LRU.
        """
        if not self.is_available() or self.sentence_model is None:
            self._logger.warning("Semantic search engine not available or model not loaded, cannot encode text.")
            return None
        if not isinstance(text, str):
            self._logger.error(f"Invalid input type for encode: Expected str, got {type(text)}")
            return None
        try:
            embedding = self.sentence_model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            self._logger.error(f"Failed to encode text '{text[:50]}...': {e}")
            return None

    def batch_encode(self, texts: List[str], batch_size: int = 32) -> Optional[List[List[float]]]:
        """
        Generate embeddings for a list of texts in batches.
        This method does not use LRU cache directly, but individual encodes might if called separately.
        """
        if not self.is_available() or self.sentence_model is None:
            self._logger.warning("Semantic search engine not available or model not loaded, cannot batch encode texts.")
            return None
        if not texts:
            return []
        if not all(isinstance(t, str) for t in texts):
            self._logger.error("Invalid input type for batch_encode: All elements must be strings.")
            return None
        try:
            embeddings = self.sentence_model.encode(texts, batch_size=batch_size, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            self._logger.error(f"Failed to batch encode texts: {e}")
            return None

    def search(self, query: str, collection_name: str, limit: int = 10, min_similarity: float = 0.7,
               metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        Perform semantic search in a specified ChromaDB collection.

        Args:
            query: The natural language query string.
            collection_name: The name of the ChromaDB collection to search.
            limit: The maximum number of results to return.
            min_similarity: Minimum similarity score to include a result (0.0 to 1.0).
            metadata_filter: Optional dictionary for metadata filtering (ChromaDB 'where' clause).

        Returns:
            A list of dictionaries, each containing 'id', 'document', 'metadata', and 'similarity_score'.
        """
        if not self.is_available() or self.chroma_connector is None:
            self._logger.warning("Semantic search engine or ChromaDB connector not available, cannot perform search.")
            return []

        query_embedding = self.encode(query)
        if query_embedding is None:
            self._logger.error("Failed to generate query embedding for search.")
            return []

        try:
            self._logger.info(f"Performing semantic search for query: '{query}' in collection '{collection_name}'")
            results = self.chroma_connector.search_documents(
                collection_name=collection_name,
                query_embedding=query_embedding,
                n_results=limit,
                min_similarity=min_similarity,
                where_clause=metadata_filter
            )
            return results
        except Exception as e:
            self._logger.error(f"Semantic search failed: {e}")
            return []

    def get_embedding_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the embedding process, including LRU cache info.
        """
        cache_info = self.encode.cache_info()
        return {
            "cache_hits": cache_info.hits,
            "cache_misses": cache_info.misses,
            "cache_current_size": cache_info.currsize,
            "cache_max_size": cache_info.maxsize,
            "model_name": self.model_name if self.sentence_model else "N/A",
            "chroma_db_available": self.chroma_connector.is_available() if self.chroma_connector else False,
            "engine_initialized": self._is_initialized
        }

