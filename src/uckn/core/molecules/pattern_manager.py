"""
UCKN Pattern Manager Molecule
Handles CRUD operations for knowledge patterns
"""

from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime
import logging

from ..atoms.semantic_search import SemanticSearch
from ...storage import ChromaDBConnector


class PatternManager:
    """Manages knowledge patterns with ChromaDB storage and semantic search"""
    
    def __init__(self, chroma_connector: ChromaDBConnector, semantic_search: SemanticSearch):
        self.chroma_connector = chroma_connector
        self.semantic_search = semantic_search
        self._logger = logging.getLogger(__name__)
    
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