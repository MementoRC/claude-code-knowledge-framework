"""
UCKN Error Solution Manager Molecule
Handles CRUD operations for error solutions
"""

from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime
import logging

from ..atoms.semantic_search import SemanticSearch
from ...storage import ChromaDBConnector


class ErrorSolutionManager:
    """Manages error solutions with ChromaDB storage and semantic search"""
    
    def __init__(self, chroma_connector: ChromaDBConnector, semantic_search: SemanticSearch):
        self.chroma_connector = chroma_connector
        self.semantic_search = semantic_search
        self._logger = logging.getLogger(__name__)
    
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

        # Generate embedding
        embedding = self.semantic_search.encode(document_text)
        if embedding is None:
            self._logger.error(f"Failed to generate embedding for solution {solution_id}.")
            return None

        # Add/update timestamps in metadata
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

        Args:
            solution_id: The ID of the solution to retrieve.

        Returns:
            A dictionary containing the solution details, or None if not found.
        """
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB not available, cannot retrieve error solution.")
            return None
        return self.chroma_connector.get_document(collection_name="error_solutions", doc_id=solution_id)

    def search_error_solutions(
        self,
        error_query: str,
        limit: int = 10,
        min_similarity: float = 0.7,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for error solutions using semantic similarity.

        Args:
            error_query: The error message or description to search for.
            limit: Maximum number of results to return.
            min_similarity: Minimum similarity score for results.
            metadata_filter: Optional dictionary for filtering results by metadata.

        Returns:
            List of relevant solution records with similarity scores.
        """
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB not available, cannot search error solutions.")
            return []
        if not self.semantic_search.is_available():
            self._logger.warning("Semantic search not available, cannot generate query embedding.")
            return []

        query_embedding = self.semantic_search.encode(error_query)
        if query_embedding is None:
            self._logger.error("Failed to generate query embedding for error search.")
            return []

        results = self.chroma_connector.search_documents(
            collection_name="error_solutions",
            query_embedding=query_embedding,
            n_results=limit,
            min_similarity=min_similarity,
            where_clause=metadata_filter
        )
        return results

    def update_error_solution(self, solution_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing error solution in the 'error_solutions' collection.

        Args:
            solution_id: The ID of the solution to update.
            updates: Dictionary of fields to update. Can include 'document' or 'metadata'.

        Returns:
            True if updated successfully, False otherwise.
        """
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB not available, cannot update error solution.")
            return False

        document_text = updates.get("document")
        metadata = updates.get("metadata")
        embedding = None

        if document_text and self.semantic_search.is_available():
            embedding = self.semantic_search.encode(document_text)
            if embedding is None:
                self._logger.error(f"Failed to generate new embedding for solution {solution_id} during update.")
                return False
        elif document_text:
            self._logger.warning("Semantic search not available, cannot re-generate embedding for updated document text.")

        # Update timestamp in metadata if present
        if metadata is not None:
            metadata["updated_at"] = datetime.now().isoformat()

        return self.chroma_connector.update_document(
            collection_name="error_solutions",
            doc_id=solution_id,
            document=document_text,
            embedding=embedding,
            metadata=metadata
        )

    def delete_error_solution(self, solution_id: str) -> bool:
        """
        Delete an error solution from the 'error_solutions' collection.

        Args:
            solution_id: The ID of the solution to delete.

        Returns:
            True if deleted successfully, False otherwise.
        """
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB not available, cannot delete error solution.")
            return False
        return self.chroma_connector.delete_document(collection_name="error_solutions", doc_id=solution_id)