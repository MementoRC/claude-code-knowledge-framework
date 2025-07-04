import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from functools import lru_cache

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
    from uckn.storage.chromadb_connector import ChromaDBConnector
    CHROMADB_CONNECTOR_AVAILABLE = True
except ImportError:
    logging.getLogger(__name__).warning(
        "ChromaDBConnector not found. "
        "ChromaDB integration for semantic search will be disabled."
    )
    ChromaDBConnector = None
    CHROMADB_CONNECTOR_AVAILABLE = False

try:
    from .multi_modal_embeddings import MultiModalEmbeddings
    MULTIMODAL_EMBEDDINGS_AVAILABLE = True
except ImportError:
    logging.getLogger(__name__).warning(
        "MultiModalEmbeddings not found. "
        "Multi-modal search capabilities will be limited."
    )
    MultiModalEmbeddings = None
    MULTIMODAL_EMBEDDINGS_AVAILABLE = False

def _tech_stack_match(query_stack: Optional[List[str]], doc_stack: Optional[List[str]]) -> float:
    """
    Compute a tech stack compatibility score between two stacks.
    Returns a float between 0.0 and 1.0.
    """
    if not query_stack or not doc_stack:
        return 0.5  # Neutral if unknown
    set_query = set([s.lower() for s in query_stack])
    set_doc = set([s.lower() for s in doc_stack])
    if not set_query or not set_doc:
        return 0.5
    intersection = set_query & set_doc
    union = set_query | set_doc
    if not union:
        return 0.5
    return len(intersection) / len(union)

class EnhancedSemanticSearchEngine:
    """
    Enhanced semantic search engine using sentence transformers and ChromaDB.

    Provides embedding-based similarity search for knowledge management with
    features like LRU caching, batch processing, and robust error handling.
    """

    def __init__(self, knowledge_dir: str = ".uckn/knowledge",
                 model_name: str = "all-MiniLM-L6-v2",
                 device: str = "cpu",
                 embedding_atom: Optional[MultiModalEmbeddings] = None,
                 chroma_connector: Optional[ChromaDBConnector] = None):
        self._logger = logging.getLogger(__name__)
        self.knowledge_dir = knowledge_dir
        self.model_name = model_name
        self.device = device
        self.sentence_model: Optional[SentenceTransformer] = None
        self.chroma_connector: Optional[ChromaDBConnector] = chroma_connector
        self.embedding_atom: Optional[MultiModalEmbeddings] = embedding_atom
        self._is_initialized = False

        self._initialize_components()

    def _initialize_components(self) -> None:
        """Initializes the sentence transformer model, ChromaDB connector, and MultiModalEmbeddings."""
        try:
            if SENTENCE_TRANSFORMER_AVAILABLE:
                self._init_sentence_transformer()
            else:
                self._logger.warning("SentenceTransformer not available, semantic encoding will be disabled.")

            if CHROMADB_CONNECTOR_AVAILABLE and not self.chroma_connector:
                self._init_chromadb()
            elif not CHROMADB_CONNECTOR_AVAILABLE:
                self._logger.warning("ChromaDBConnector not available, ChromaDB search will be disabled.")

            # Initialize MultiModalEmbeddings if not provided
            if MULTIMODAL_EMBEDDINGS_AVAILABLE and not self.embedding_atom:
                self._init_multimodal_embeddings()
            elif not MULTIMODAL_EMBEDDINGS_AVAILABLE:
                self._logger.warning("MultiModalEmbeddings not available, multi-modal search will be disabled.")

            # Check initialization status
            has_embeddings = self.sentence_model or self.embedding_atom
            has_storage = self.chroma_connector and self.chroma_connector.is_available()
            
            if has_embeddings and has_storage:
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

    def _init_multimodal_embeddings(self) -> None:
        """Initializes the MultiModalEmbeddings."""
        try:
            self.embedding_atom = MultiModalEmbeddings()
            self._logger.info("MultiModalEmbeddings initialized successfully.")
        except Exception as e:
            self.embedding_atom = None
            self._logger.error(f"Failed to initialize MultiModalEmbeddings: {e}")

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

    # --- Multi-Modal and Advanced Search Methods ---

    def _get_collection(self, collection_type: str) -> str:
        """Map collection type to collection name."""
        return collection_type  # Direct mapping for now

    def _get_success_rate(self, metadata: Dict[str, Any]) -> float:
        """Extract success rate from metadata."""
        return float(metadata.get("success_rate", 0.5))

    def _extract_tech_stack(self, metadata: Dict[str, Any]) -> List[str]:
        """Extract technology stack from metadata."""
        tech_stack = metadata.get("technologies", [])
        if isinstance(tech_stack, str):
            return [tech_stack]
        elif isinstance(tech_stack, list):
            return tech_stack
        return []

    def _rank_results(
        self,
        results: List[Dict[str, Any]],
        query_tech_stack: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Advanced ranking of search results considering:
        - Base similarity score
        - Technology stack compatibility
        - Historical success rate
        """
        if not results:
            return results

        for result in results:
            metadata = result.get("metadata", {})
            
            # Base similarity score (from vector search)
            base_score = result.get("similarity_score", 0.0)
            
            # Technology stack compatibility bonus
            doc_tech_stack = self._extract_tech_stack(metadata)
            tech_score = _tech_stack_match(query_tech_stack, doc_tech_stack)
            
            # Success rate bonus
            success_rate = self._get_success_rate(metadata)
            
            # Combined score with weighted components
            combined_score = (
                base_score * 0.6 +      # 60% similarity
                tech_score * 0.25 +     # 25% tech compatibility  
                success_rate * 0.15     # 15% success rate
            )
            
            result["combined_score"] = combined_score
            result["tech_compatibility"] = tech_score

        # Sort by combined score (descending)
        ranked = sorted(results, key=lambda x: x["combined_score"], reverse=True)
        return ranked

    def _filter_by_tech_stack(
        self,
        results: List[Dict[str, Any]],
        tech_stack: Optional[List[str]],
        min_compatibility: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Filter results by technology stack compatibility."""
        if not tech_stack:
            return results
        
        filtered = []
        for result in results:
            metadata = result.get("metadata", {})
            doc_tech_stack = self._extract_tech_stack(metadata)
            compatibility = _tech_stack_match(tech_stack, doc_tech_stack)
            
            if compatibility >= min_compatibility:
                result["tech_compatibility"] = compatibility
                filtered.append(result)
        
        return filtered

    @lru_cache(maxsize=128)
    def _cached_embed(self, data: str, data_type: str) -> Optional[List[float]]:
        """Use MultiModalEmbeddings for embedding generation with caching."""
        if self.embedding_atom:
            return self.embedding_atom.embed(data, data_type=data_type)
        elif self.sentence_model and data_type == "text":
            # Fallback to SentenceTransformer for text
            return self.sentence_model.encode(data).tolist()
        return None

    def _embed_query(self, text=None, code=None, error=None) -> Optional[List[float]]:
        """Generate embeddings for multi-modal queries."""
        if not self.embedding_atom:
            # Fallback: use text embedding if available
            if text and self.sentence_model:
                return self.sentence_model.encode(text).tolist()
            return None
            
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

    def _parse_tech_stack(self, tech_stack) -> Optional[List[str]]:
        """Parse technology stack from various input formats."""
        if tech_stack is None:
            return None
        elif isinstance(tech_stack, str):
            # Split by common separators
            return [s.strip() for s in tech_stack.replace(",", " ").split() if s.strip()]
        elif isinstance(tech_stack, list):
            return [str(s).strip() for s in tech_stack if str(s).strip()]
        else:
            return None

    def search_by_text(self, query_text: str, tech_stack=None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Semantic search for code patterns and error solutions by text.

        Args:
            query_text: Natural language query.
            tech_stack: Optional technology stack filter (str or list).
            limit: Max results.

        Returns:
            Ranked list of matching documents.
        """
        if not self.is_available():
            self._logger.warning("Search engine not available")
            return []
            
        query_tech_stack = self._parse_tech_stack(tech_stack)
        embedding = self._cached_embed(query_text, "text")
        if embedding is None:
            self._logger.warning("Failed to generate embedding for text query.")
            return []
            
        results = []
        for collection in ("code_patterns", "error_solutions"):
            res = self.search(
                query=query_text,
                collection_name=collection,
                limit=limit,
                min_similarity=0.7
            )
            results.extend(res)
            
        # Apply technology stack filtering
        if query_tech_stack:
            results = self._filter_by_tech_stack(results, query_tech_stack)
            
        ranked = self._rank_results(results, query_tech_stack)
        return ranked[:limit]

    def search_by_code(self, code_snippet: str, tech_stack=None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Semantic search for code patterns and error solutions by code snippet.

        Args:
            code_snippet: Code string.
            tech_stack: Optional technology stack filter (str or list).
            limit: Max results.

        Returns:
            Ranked list of matching documents.
        """
        if not self.is_available():
            self._logger.warning("Search engine not available")
            return []
            
        query_tech_stack = self._parse_tech_stack(tech_stack)
        embedding = self._cached_embed(code_snippet, "code")
        if embedding is None:
            self._logger.warning("Failed to generate embedding for code query.")
            return []
            
        results = []
        for collection in ("code_patterns", "error_solutions"):
            if self.chroma_connector:
                res = self.chroma_connector.search_by_embedding(
                    collection_name=collection,
                    query_embedding=embedding,
                    n_results=limit,
                    where=None
                )
                for result in res:
                    result["similarity_score"] = 1.0 - result.get("distance", 0.0)
                results.extend(res)
                
        # Apply technology stack filtering
        if query_tech_stack:
            results = self._filter_by_tech_stack(results, query_tech_stack)
            
        ranked = self._rank_results(results, query_tech_stack)
        return ranked[:limit]

    def search_by_error(self, error_message: str, tech_stack=None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Semantic search for error solutions by error message.

        Args:
            error_message: Error message string.
            tech_stack: Optional technology stack filter (str or list).
            limit: Max results.

        Returns:
            Ranked list of matching documents.
        """
        if not self.is_available():
            self._logger.warning("Search engine not available")
            return []
            
        query_tech_stack = self._parse_tech_stack(tech_stack)
        embedding = self._cached_embed(error_message, "error")
        if embedding is None:
            self._logger.warning("Failed to generate embedding for error query.")
            return []
            
        results = []
        # Focus on error_solutions collection for error queries
        for collection in ("error_solutions", "code_patterns"):
            if self.chroma_connector:
                res = self.chroma_connector.search_by_embedding(
                    collection_name=collection,
                    query_embedding=embedding,
                    n_results=limit,
                    where=None
                )
                for result in res:
                    result["similarity_score"] = 1.0 - result.get("distance", 0.0)
                results.extend(res)
                
        # Apply technology stack filtering
        if query_tech_stack:
            results = self._filter_by_tech_stack(results, query_tech_stack)
            
        ranked = self._rank_results(results, query_tech_stack)
        return ranked[:limit]

    def search_multi_modal(
        self,
        text: Optional[str] = None,
        code: Optional[str] = None,
        error: Optional[str] = None,
        tech_stack=None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
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
        if not self.is_available():
            self._logger.warning("Search engine not available")
            return []
            
        query_tech_stack = self._parse_tech_stack(tech_stack)
        embedding = self._embed_query(text=text, code=code, error=error)
        if embedding is None:
            self._logger.warning("Failed to generate embedding for multi-modal query.")
            return []
            
        results = []
        for collection in ("code_patterns", "error_solutions"):
            if self.chroma_connector:
                res = self.chroma_connector.search_by_embedding(
                    collection_name=collection,
                    query_embedding=embedding,
                    n_results=limit,
                    where=None
                )
                for result in res:
                    result["similarity_score"] = 1.0 - result.get("distance", 0.0)
                results.extend(res)
                
        # Apply technology stack filtering
        if query_tech_stack:
            results = self._filter_by_tech_stack(results, query_tech_stack)
            
        ranked = self._rank_results(results, query_tech_stack)
        return ranked[:limit]

