"""
UCKN Core Framework Components
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime
import logging

# Import the new ChromaDBConnector
from uckn.storage import ChromaDBConnector

# Import the existing SemanticSearchEngine from the framework
# This is a READ ONLY file, so we assume it's available.
try:
    from framework.core.semantic_search import SemanticSearchEngine
    SEMANTIC_SEARCH_ENGINE_AVAILABLE = True
except ImportError:
    logging.getLogger(__name__).warning(
        "framework.core.semantic_search.SemanticSearchEngine not found. "
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


class KnowledgeManager:
    """Core knowledge management system using ChromaDB for storage."""

    def __init__(self, knowledge_dir: str = ".uckn/knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger(__name__)

        # Initialize ChromaDB connector
        self.chroma_connector = ChromaDBConnector(db_path=str(self.knowledge_dir / "chroma_db"))
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB is not available. Knowledge storage and retrieval will be limited.")

        # Initialize Semantic Search for embeddings
        self.semantic_search = SemanticSearch(knowledge_dir=str(self.knowledge_dir))
        if not self.semantic_search.is_available():
            self._logger.warning("Semantic search model not available. Embeddings cannot be generated.")

    def add_pattern(self, pattern_data: Dict[str, Any]) -> Optional[str]:
        """
        Add a new knowledge pattern to the 'code_patterns' collection.

        Args:
            pattern_data: Dictionary containing pattern details.
                          Must include 'document' (text content) and 'metadata'.
                          Metadata must conform to 'code_patterns' schema.

        Returns:
            The pattern_id if added successfully, None otherwise.
        """
        if not self.chroma_connector.is_available():
            self._logger.error("ChromaDB not available, cannot add pattern.")
            return None
        if not self.semantic_search.is_available():
            self._logger.error("Semantic search not available, cannot generate embeddings for pattern.")
            return None

        pattern_id = pattern_data.get("pattern_id", str(uuid.uuid4()))
        document_text = pattern_data.get("document")
        metadata = pattern_data.get("metadata", {})

        if not document_text:
            self._logger.error("Pattern data must include 'document' text for embedding.")
            return None

        # Generate embedding
        embedding = self.semantic_search.encode(document_text)
        if embedding is None:
            self._logger.error(f"Failed to generate embedding for pattern {pattern_id}.")
            return None

        # Add/update timestamps in metadata
        now_iso = datetime.now().isoformat()
        metadata["pattern_id"] = pattern_id
        metadata["created_at"] = metadata.get("created_at", now_iso)
        metadata["updated_at"] = now_iso

        success = self.chroma_connector.add_document(
            collection_name="code_patterns",
            doc_id=pattern_id,
            document=document_text,
            embedding=embedding,
            metadata=metadata
        )
        return pattern_id if success else None

    def get_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific pattern from the 'code_patterns' collection.

        Args:
            pattern_id: The ID of the pattern to retrieve.

        Returns:
            A dictionary containing the pattern details, or None if not found.
        """
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB not available, cannot retrieve pattern.")
            return None
        return self.chroma_connector.get_document(collection_name="code_patterns", doc_id=pattern_id)

    def update_pattern(self, pattern_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing pattern in the 'code_patterns' collection.

        Args:
            pattern_id: The ID of the pattern to update.
            updates: Dictionary of fields to update. Can include 'document' or 'metadata'.

        Returns:
            True if updated successfully, False otherwise.
        """
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB not available, cannot update pattern.")
            return False

        document_text = updates.get("document")
        metadata = updates.get("metadata")
        embedding = None

        if document_text and self.semantic_search.is_available():
            embedding = self.semantic_search.encode(document_text)
            if embedding is None:
                self._logger.error(f"Failed to generate new embedding for pattern {pattern_id} during update.")
                return False
        elif document_text:
            self._logger.warning("Semantic search not available, cannot re-generate embedding for updated document text.")

        # Update timestamp in metadata if present
        if metadata is not None:
            metadata["updated_at"] = datetime.now().isoformat()

        return self.chroma_connector.update_document(
            collection_name="code_patterns",
            doc_id=pattern_id,
            document=document_text,
            embedding=embedding,
            metadata=metadata
        )

    def delete_pattern(self, pattern_id: str) -> bool:
        """
        Delete a pattern from the 'code_patterns' collection.

        Args:
            pattern_id: The ID of the pattern to delete.

        Returns:
            True if deleted successfully, False otherwise.
        """
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB not available, cannot delete pattern.")
            return False
        return self.chroma_connector.delete_document(collection_name="code_patterns", doc_id=pattern_id)

    def search_patterns(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.7,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for knowledge patterns using semantic similarity.

        Args:
            query: The search query string.
            limit: Maximum number of results to return.
            min_similarity: Minimum similarity score for results.
            metadata_filter: Optional dictionary for filtering results by metadata.

        Returns:
            List of relevant pattern records with similarity scores.
        """
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB not available, cannot search patterns.")
            return []
        if not self.semantic_search.is_available():
            self._logger.warning("Semantic search not available, cannot generate query embedding.")
            return []

        query_embedding = self.semantic_search.encode(query)
        if query_embedding is None:
            self._logger.error("Failed to generate query embedding.")
            return []

        results = self.chroma_connector.search_documents(
            collection_name="code_patterns",
            query_embedding=query_embedding,
            n_results=limit,
            min_similarity=min_similarity,
            where_clause=metadata_filter
        )
        return results

    def add_error_solution(self, solution_data: Dict[str, Any]) -> Optional[str]:
        """
        Add a new error solution to the 'error_solutions' collection.

        Args:
            solution_data: Dictionary containing solution details.
                           Must include 'document' (error message/description) and 'metadata'.
                           Metadata must conform to 'error_solutions' schema.

        Returns:
            The solution_id if added successfully, None otherwise.
        """
        if not self.chroma_connector.is_available():
            self._logger.error("ChromaDB not available, cannot add error solution.")
            return None
        if not self.semantic_search.is_available():
            self._logger.error("Semantic search not available, cannot generate embeddings for error solution.")
            return None

        solution_id = solution_data.get("solution_id", str(uuid.uuid4()))
        document_text = solution_data.get("document")
        metadata = solution_data.get("metadata", {})

        if not document_text:
            self._logger.error("Solution data must include 'document' text for embedding.")
            return None

        embedding = self.semantic_search.encode(document_text)
        if embedding is None:
            self._logger.error(f"Failed to generate embedding for solution {solution_id}.")
            return None

        now_iso = datetime.now().isoformat()
        metadata["solution_id"] = solution_id
        metadata["created_at"] = metadata.get("created_at", now_iso)
        metadata["updated_at"] = now_iso

        success = self.chroma_connector.add_document(
            collection_name="error_solutions",
            doc_id=solution_id,
            document=document_text,
            embedding=embedding,
            metadata=metadata
        )
        return solution_id if success else None

    def get_error_solution(self, solution_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific error solution from the 'error_solutions' collection.
        """
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB not available, cannot retrieve error solution.")
            return None
        return self.chroma_connector.get_document(collection_name="error_solutions", doc_id=solution_id)

    def search_error_solutions(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.7,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for error solutions using semantic similarity.
        """
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB not available, cannot search error solutions.")
            return []
        if not self.semantic_search.is_available():
            self._logger.warning("Semantic search not available, cannot generate query embedding.")
            return []

        query_embedding = self.semantic_search.encode(query)
        if query_embedding is None:
            self._logger.error("Failed to generate query embedding.")
            return []

        results = self.chroma_connector.search_documents(
            collection_name="error_solutions",
            query_embedding=query_embedding,
            n_results=limit,
            min_similarity=min_similarity,
            where_clause=metadata_filter
        )
        return results

    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about the stored knowledge."""
        if not self.chroma_connector.is_available():
            return {
                "status": "ChromaDB Unavailable",
                "code_patterns_count": 0,
                "error_solutions_count": 0,
                "semantic_search_available": self.semantic_search.is_available()
            }
        return {
            "status": "Operational",
            "code_patterns_count": self.chroma_connector.count_documents("code_patterns"),
            "error_solutions_count": self.chroma_connector.count_documents("error_solutions"),
            "semantic_search_available": self.semantic_search.is_available()
        }


class TechStackDetector:
    """Detect project technology stack"""

    def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """Analyze project for technology stack"""
        path = Path(project_path)

        stack = {
            "languages": [],
            "package_managers": [],
            "frameworks": [],
            "testing": [],
            "ci_cd": []
        }

        # Detect Python
        if (path / "pyproject.toml").exists():
            stack["languages"].append("Python")
            stack["package_managers"].append("pip/poetry/pixi")

        if (path / "requirements.txt").exists():
            stack["package_managers"].append("pip")

        # Detect JavaScript/Node.js
        if (path / "package.json").exists():
            stack["languages"].append("JavaScript")
            stack["package_managers"].append("npm")

        # Detect testing frameworks
        if (path / "pytest.ini").exists() or "pytest" in str(path):
            stack["testing"].append("pytest")

        # Detect CI/CD
        if (path / ".github" / "workflows").exists():
            stack["ci_cd"].append("GitHub Actions")

        return stack
