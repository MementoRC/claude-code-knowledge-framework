"""
UCKN Error Solution Manager Molecule
Handles CRUD operations for error solutions
"""

import logging
import uuid
from datetime import datetime
from typing import Any

from ...storage import UnifiedDatabase  # Changed from ChromaDBConnector
from ..atoms.semantic_search import SemanticSearch


class ErrorSolutionManager:
    """Manages error solutions with UnifiedDatabase storage and semantic search"""

    def __init__(self, unified_db: UnifiedDatabase, semantic_search: SemanticSearch):
        self.unified_db = unified_db  # Changed from chroma_connector
        self.semantic_search = semantic_search
        self._logger = logging.getLogger(__name__)

    def add_error_solution(self, solution_data: dict[str, Any]) -> str | None:
        """
        Add a new error solution to the 'error_solutions' collection.

        Args:
            solution_data: Dictionary containing solution details.
                           Must include 'document' (error message/description) and 'metadata'.
                           Metadata must conform to 'error_solutions' schema.
                           Can optionally include 'project_id'.

        Returns:
            The solution_id if added successfully, None otherwise.
        """
        if not self.unified_db.is_available():
            self._logger.error(
                "Unified Database not available, cannot add error solution."
            )
            return None
        if not self.semantic_search.is_available():
            self._logger.error(
                "Semantic search not available, cannot generate embeddings for error solution."
            )
            return None

        solution_id = solution_data.get("solution_id", str(uuid.uuid4()))
        document_text = solution_data.get("document")
        metadata = solution_data.get("metadata", {})
        project_id = solution_data.get("project_id")

        if not document_text:
            self._logger.error(
                "Solution data must include 'document' text for embedding."
            )
            return None

        # Generate embedding
        embedding = self.semantic_search.encode(document_text)
        if embedding is None:
            self._logger.error(
                f"Failed to generate embedding for solution {solution_id}."
            )
            return None

        # Add/update timestamps in metadata (these will be stored in PG metadata_json and specific columns)
        now_iso = datetime.now().isoformat()
        metadata["solution_id"] = solution_id  # Ensure ID is in metadata for ChromaDB
        metadata["created_at"] = metadata.get("created_at", now_iso)
        metadata["updated_at"] = now_iso

        # UnifiedDatabase handles splitting data to PG and Chroma
        success = self.unified_db.add_error_solution(
            document_text=document_text,
            embedding=embedding,
            metadata=metadata,
            solution_id=solution_id,
            project_id=project_id,
        )
        return solution_id if success else None

    def get_error_solution(self, solution_id: str) -> dict[str, Any] | None:
        """
        Retrieve a specific error solution from the Unified Database.

        Args:
            solution_id: The ID of the solution to retrieve.

        Returns:
            A dictionary containing the solution details, or None if not found.
        """
        if not self.unified_db.is_available():
            self._logger.warning(
                "Unified Database not available, cannot retrieve error solution."
            )
            return None
        return self.unified_db.get_error_solution(solution_id)

    def search_error_solutions(
        self,
        error_query: str,
        limit: int = 10,
        min_similarity: float = 0.7,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
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
        if not self.unified_db.is_available():
            self._logger.warning(
                "Unified Database not available, cannot search error solutions."
            )
            return []
        if not self.semantic_search.is_available():
            self._logger.warning(
                "Semantic search not available, cannot generate query embedding."
            )
            return []

        query_embedding = self.semantic_search.encode(error_query)
        if query_embedding is None:
            self._logger.error("Failed to generate query embedding for error search.")
            return []

        # UnifiedDatabase handles searching ChromaDB and fetching metadata from PG
        results = self.unified_db.search_error_solutions(
            query_embedding=query_embedding,
            n_results=limit,
            min_similarity=min_similarity,
            metadata_filter=metadata_filter,
        )
        return results

    def update_error_solution(self, solution_id: str, updates: dict[str, Any]) -> bool:
        """
        Update an existing error solution in the Unified Database.

        Args:
            solution_id: The ID of the solution to update.
            updates: Dictionary of fields to update. Can include 'document' or 'metadata' or 'project_id'.

        Returns:
            True if updated successfully, False otherwise.
        """
        if not self.unified_db.is_available():
            self._logger.warning(
                "Unified Database not available, cannot update error solution."
            )
            return False

        document_text = updates.get("document")
        metadata = updates.get("metadata")
        project_id = updates.get("project_id")
        embedding = None

        if document_text and self.semantic_search.is_available():
            embedding = self.semantic_search.encode(document_text)
            if embedding is None:
                self._logger.error(
                    f"Failed to generate new embedding for solution {solution_id} during update."
                )
                return False
        elif document_text:
            self._logger.warning(
                "Semantic search not available, cannot re-generate embedding for updated document text."
            )

        # Update timestamp in metadata
        if metadata is None:
            metadata = {}
        metadata["updated_at"] = datetime.now().isoformat()

        # UnifiedDatabase handles updating both PG and Chroma
        return self.unified_db.update_error_solution(
            solution_id=solution_id,
            document_text=document_text,
            embedding=embedding,
            metadata=metadata,
            project_id=project_id,
        )

    def delete_error_solution(self, solution_id: str) -> bool:
        """
        Delete an error solution from the Unified Database.

        Args:
            solution_id: The ID of the solution to delete.

        Returns:
            True if deleted successfully, False otherwise.
        """
        if not self.unified_db.is_available():
            self._logger.warning(
                "Unified Database not available, cannot delete error solution."
            )
            return False
        # UnifiedDatabase handles deleting from both PG and Chroma
        return self.unified_db.delete_error_solution(solution_id)
