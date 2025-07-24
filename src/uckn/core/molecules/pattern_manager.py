"""
UCKN Pattern Manager Molecule
Handles CRUD operations for knowledge patterns
"""

import logging
import uuid
from datetime import datetime
from typing import Any

from ...storage import UnifiedDatabase  # Changed from ChromaDBConnector
from ..atoms.semantic_search import SemanticSearch


class PatternManager:
    """Manages knowledge patterns with UnifiedDatabase storage and semantic search"""

    def __init__(self, unified_db: UnifiedDatabase, semantic_search: SemanticSearch):
        self.unified_db = unified_db  # Changed from chroma_connector
        self.semantic_search = semantic_search
        self._logger = logging.getLogger(__name__)

    def add_pattern(self, pattern_data: dict[str, Any]) -> str | None:
        """
        Add a new knowledge pattern to the Unified Database.

        Args:
            pattern_data: Dictionary containing pattern details.
                          Must include 'document' (text content) and 'metadata'.
                          Metadata must conform to 'code_patterns' schema.
                          Can optionally include 'project_id'.

        Returns:
            The pattern_id if added successfully, None otherwise.
        """
        if not self.unified_db.is_available():
            self._logger.error("Unified Database not available, cannot add pattern.")
            return None
        if not self.semantic_search.is_available():
            self._logger.error(
                "Semantic search not available, cannot generate embeddings for pattern."
            )
            return None

        pattern_id = pattern_data.get("pattern_id", str(uuid.uuid4()))
        document_text = pattern_data.get("document")
        metadata = pattern_data.get("metadata", {})
        project_id = pattern_data.get("project_id")

        if not document_text:
            self._logger.error(
                "Pattern data must include 'document' text for embedding."
            )
            return None

        # Generate embedding
        embedding = self.semantic_search.encode(document_text)
        if embedding is None:
            self._logger.error(
                f"Failed to generate embedding for pattern {pattern_id}."
            )
            return None

        # Add/update timestamps in metadata (these will be stored in PG metadata_json and specific columns)
        now_iso = datetime.now().isoformat()
        metadata["pattern_id"] = pattern_id  # Ensure ID is in metadata for ChromaDB
        metadata["created_at"] = metadata.get("created_at", now_iso)
        metadata["updated_at"] = now_iso

        # UnifiedDatabase handles splitting data to PG and Chroma
        success = self.unified_db.add_pattern(
            document_text=document_text,
            embedding=embedding,
            metadata=metadata,
            pattern_id=pattern_id,
            project_id=project_id,
        )
        return pattern_id if success else None

    def get_pattern(self, pattern_id: str) -> dict[str, Any] | None:
        """
        Retrieve a specific pattern from the Unified Database.

        Args:
            pattern_id: The ID of the pattern to retrieve.

        Returns:
            A dictionary containing the pattern details, or None if not found.
        """
        if not self.unified_db.is_available():
            self._logger.warning(
                "Unified Database not available, cannot retrieve pattern."
            )
            return None
        return self.unified_db.get_pattern(pattern_id)

    def update_pattern(self, pattern_id: str, updates: dict[str, Any]) -> bool:
        """
        Update an existing pattern in the Unified Database.

        Args:
            pattern_id: The ID of the pattern to update.
            updates: Dictionary of fields to update. Can include 'document', 'metadata', or 'project_id'.

        Returns:
            True if updated successfully, False otherwise.
        """
        if not self.unified_db.is_available():
            self._logger.warning(
                "Unified Database not available, cannot update pattern."
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
                    f"Failed to generate new embedding for pattern {pattern_id} during update."
                )
                return False
        elif document_text:
            self._logger.warning(
                "Semantic search not available, cannot re-generate embedding for updated document text."
            )

        # Update timestamp in metadata if present
        if metadata is not None:
            metadata["updated_at"] = datetime.now().isoformat()

        # UnifiedDatabase handles updating both PG and Chroma
        return self.unified_db.update_pattern(
            pattern_id=pattern_id,
            document_text=document_text,
            embedding=embedding,
            metadata=metadata,
            project_id=project_id,
        )

    def delete_pattern(self, pattern_id: str) -> bool:
        """
        Delete a pattern from the Unified Database.

        Args:
            pattern_id: The ID of the pattern to delete.

        Returns:
            True if deleted successfully, False otherwise.
        """
        if not self.unified_db.is_available():
            self._logger.warning(
                "Unified Database not available, cannot delete pattern."
            )
            return False
        # UnifiedDatabase handles deleting from both PG and Chroma
        return self.unified_db.delete_pattern(pattern_id)

    def search_patterns(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.7,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
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
        if not self.unified_db.is_available():
            self._logger.warning(
                "Unified Database not available, cannot search patterns."
            )
            return []
        if not self.semantic_search.is_available():
            self._logger.warning(
                "Semantic search not available, cannot generate query embedding."
            )
            return []

        query_embedding = self.semantic_search.encode(query)
        if query_embedding is None:
            self._logger.error("Failed to generate query embedding.")
            return []

        # UnifiedDatabase handles searching ChromaDB and fetching metadata from PG
        results = self.unified_db.search_patterns(
            query_embedding=query_embedding,
            n_results=limit,
            min_similarity=min_similarity,
            metadata_filter=metadata_filter,
        )
        return results
