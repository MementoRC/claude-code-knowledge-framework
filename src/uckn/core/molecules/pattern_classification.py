"""
UCKN Pattern Classification Molecule

Manages a hierarchical classification system for knowledge patterns,
allowing patterns to be categorized for efficient retrieval and organization.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from ...storage.chromadb_connector import ChromaDBConnector

class PatternClassification:
    """
    Manages a hierarchical classification system for knowledge patterns.

    Categories are stored in a dedicated ChromaDB collection, allowing for
    parent-child relationships and multi-category assignment for patterns.
    """

    CLASSIFICATION_COLLECTION = "pattern_classifications"
    PATTERN_COLLECTION = "code_patterns" # Reference to patterns, not managed here

    def __init__(self, chroma_connector: ChromaDBConnector):
        self.chroma_connector = chroma_connector
        self._logger = logging.getLogger(__name__)
        self._ensure_classification_collection()

    def _ensure_classification_collection(self):
        """
        Ensure the pattern_classifications collection exists in ChromaDB.
        """
        if not hasattr(self.chroma_connector, "collections"):
            self._logger.error("ChromaDBConnector missing 'collections' attribute.")
            return
        if self.CLASSIFICATION_COLLECTION not in self.chroma_connector.collections:
            try:
                self.chroma_connector.collections[self.CLASSIFICATION_COLLECTION] = (
                    self.chroma_connector.client.get_or_create_collection(
                        name=self.CLASSIFICATION_COLLECTION,
                        metadata={"description": "UCKN pattern classifications and categories"}
                    )
                )
                self._logger.info(f"ChromaDB collection '{self.CLASSIFICATION_COLLECTION}' initialized.")
            except Exception as e:
                self._logger.error(f"Failed to create {self.CLASSIFICATION_COLLECTION} collection: {e}")

    def add_category(
        self, category_name: str, description: Optional[str] = None, category_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Add a new pattern category.

        Args:
            category_name: The name of the category.
            description: An optional description for the category.
            category_id: Optional, a specific ID for the category. If None, a UUID is generated.

        Returns:
            The ID of the newly created category, or None if creation failed.
        """
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB not available, cannot add category.")
            return None

        category_id = category_id or str(uuid.uuid4())
        now_iso = datetime.now().isoformat()

        metadata = {
            "category_id": category_id,
            "name": category_name,
            "description": description,
            "created_at": now_iso,
            "updated_at": now_iso,
            "patterns": []  # List of pattern_ids assigned to this category
        }

        try:
            success = self.chroma_connector.add_document(
                collection_name=self.CLASSIFICATION_COLLECTION,
                doc_id=category_id,
                document=f"Category: {category_name}", # Document content for potential future semantic search on categories
                embedding=[0.0], # Placeholder, categories are retrieved by ID/metadata, not semantic search on content
                metadata=metadata
            )
            if success:
                self._logger.info(f"Added category '{category_name}' with ID: {category_id}.")
                return category_id
            else:
                self._logger.error(f"Failed to add category '{category_name}'.")
                return None
        except Exception as e:
            self._logger.error(f"Error adding category '{category_name}': {e}")
            return None

    def get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific pattern category by its ID.

        Args:
            category_id: The ID of the category to retrieve.

        Returns:
            A dictionary containing the category details (metadata), or None if not found.
        """
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB not available, cannot retrieve category.")
            return None
        try:
            category_record = self.chroma_connector.get_document(
                collection_name=self.CLASSIFICATION_COLLECTION,
                doc_id=category_id
            )
            if category_record:
                return category_record["metadata"]
            else:
                self._logger.info(f"Category with ID '{category_id}' not found.")
                return None
        except Exception as e:
            self._logger.error(f"Error retrieving category '{category_id}': {e}")
            return None

    def update_category(
        self, category_id: str, new_name: Optional[str] = None, new_description: Optional[str] = None
    ) -> bool:
        """
        Update an existing pattern category.

        Args:
            category_id: The ID of the category to update.
            new_name: Optional new name for the category.
            new_description: Optional new description for the category.

        Returns:
            True if the category was updated successfully, False otherwise.
        """
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB not available, cannot update category.")
            return False

        category_record = self.chroma_connector.get_document(
            collection_name=self.CLASSIFICATION_COLLECTION,
            doc_id=category_id
        )
        if not category_record:
            self._logger.error(f"Category with ID '{category_id}' not found for update.")
            return False

        metadata = category_record["metadata"]
        
        # Update name and description if provided and different
        if new_name is not None and metadata.get("name") != new_name:
            metadata["name"] = new_name
        if new_description is not None and metadata.get("description") != new_description:
            metadata["description"] = new_description

        # Always update timestamp when update_category is called
        metadata["updated_at"] = datetime.now().isoformat()

        try:
            success = self.chroma_connector.update_document(
                collection_name=self.CLASSIFICATION_COLLECTION,
                doc_id=category_id,
                metadata=metadata
            )
            if success:
                self._logger.info(f"Updated category '{category_id}'.")
            else:
                self._logger.error(f"Failed to update category '{category_id}'.")
            return success
        except Exception as e:
            self._logger.error(f"Error updating category '{category_id}': {e}")
            return False

    def delete_category(self, category_id: str) -> bool:
        """
        Delete a pattern category by its ID.

        Args:
            category_id: The ID of the category to delete.

        Returns:
            True if the category was deleted successfully, False otherwise.
        """
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB not available, cannot delete category.")
            return False
        try:
            success = self.chroma_connector.delete_document(
                collection_name=self.CLASSIFICATION_COLLECTION,
                doc_id=category_id
            )
            if success:
                self._logger.info(f"Deleted category '{category_id}'.")
            else:
                self._logger.warning(f"Category with ID '{category_id}' not found or failed to delete.")
            return success
        except Exception as e:
            self._logger.error(f"Error deleting category '{category_id}': {e}")
            return False

    def assign_pattern_to_category(self, pattern_id: str, category_id: str) -> bool:
        """
        Assign a pattern to a specific category. Idempotent.

        Args:
            pattern_id: The ID of the pattern to assign.
            category_id: The ID of the category to assign the pattern to.

        Returns:
            True if the assignment was successful or already existed, False otherwise.
        """
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB not available, cannot assign pattern to category.")
            return False

        category_record = self.chroma_connector.get_document(
            collection_name=self.CLASSIFICATION_COLLECTION,
            doc_id=category_id
        )
        if not category_record:
            self._logger.error(f"Category with ID '{category_id}' not found for pattern assignment.")
            return False

        metadata = category_record["metadata"]
        patterns_in_category = set(metadata.get("patterns", []))

        if pattern_id in patterns_in_category:
            self._logger.info(f"Pattern '{pattern_id}' is already assigned to category '{category_id}'. Idempotent operation.")
            return True # Already assigned, so consider it a success

        patterns_in_category.add(pattern_id)
        metadata["patterns"] = list(patterns_in_category)
        metadata["updated_at"] = datetime.now().isoformat()

        try:
            success = self.chroma_connector.update_document(
                collection_name=self.CLASSIFICATION_COLLECTION,
                doc_id=category_id,
                metadata=metadata
            )
            if success:
                self._logger.info(f"Assigned pattern '{pattern_id}' to category '{category_id}'.")
            else:
                self._logger.error(f"Failed to assign pattern '{pattern_id}' to category '{category_id}'.")
            return success
        except Exception as e:
            self._logger.error(f"Error assigning pattern '{pattern_id}' to category '{category_id}': {e}")
            return False

    def remove_pattern_from_category(self, pattern_id: str, category_id: str) -> bool:
        """
        Remove a pattern from a specific category. Idempotent.

        Args:
            pattern_id: The ID of the pattern to remove.
            category_id: The ID of the category to remove the pattern from.

        Returns:
            True if the removal was successful or pattern was not present, False otherwise.
        """
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB not available, cannot remove pattern from category.")
            return False

        category_record = self.chroma_connector.get_document(
            collection_name=self.CLASSIFICATION_COLLECTION,
            doc_id=category_id
        )
        if not category_record:
            self._logger.error(f"Category with ID '{category_id}' not found for pattern removal.")
            return False

        metadata = category_record["metadata"]
        patterns_in_category = set(metadata.get("patterns", []))

        if pattern_id not in patterns_in_category:
            self._logger.info(f"Pattern '{pattern_id}' is not in category '{category_id}'. Idempotent operation.")
            return True # Not present, so consider it a success

        patterns_in_category.discard(pattern_id) # Use discard to avoid KeyError if somehow not present
        metadata["patterns"] = list(patterns_in_category)
        metadata["updated_at"] = datetime.now().isoformat()

        try:
            success = self.chroma_connector.update_document(
                collection_name=self.CLASSIFICATION_COLLECTION,
                doc_id=category_id,
                metadata=metadata
            )
            if success:
                self._logger.info(f"Removed pattern '{pattern_id}' from category '{category_id}'.")
            else:
                self._logger.error(f"Failed to remove pattern '{pattern_id}' from category '{category_id}'.")
            return success
        except Exception as e:
            self._logger.error(f"Error removing pattern '{pattern_id}' from category '{category_id}': {e}")
            return False

    def get_patterns_in_category(self, category_id: str) -> List[str]:
        """
        Get all pattern IDs assigned to a specific category.

        Args:
            category_id: The ID of the category.

        Returns:
            A list of pattern IDs. Returns an empty list if the category is not found
            or has no patterns assigned.
        """
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB not available, cannot get patterns in category.")
            return []
        try:
            category_record = self.chroma_connector.get_document(
                collection_name=self.CLASSIFICATION_COLLECTION,
                doc_id=category_id
            )
            if category_record:
                return category_record["metadata"].get("patterns", [])
            else:
                self._logger.info(f"Category with ID '{category_id}' not found.")
                return []
        except Exception as e:
            self._logger.error(f"Error getting patterns for category '{category_id}': {e}")
            return []

    def get_categories_for_pattern(self, pattern_id: str) -> List[Dict[str, Any]]:
        """
        Get all categories that a specific pattern is assigned to.

        Args:
            pattern_id: The ID of the pattern.

        Returns:
            A list of dictionaries, where each dictionary represents a category
            (its metadata). Returns an empty list if the pattern is not assigned
            to any categories or if ChromaDB is unavailable.
        """
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB not available, cannot get categories for pattern.")
            return []
        
        matching_categories = []
        try:
            all_categories = self.chroma_connector.get_all_documents(self.CLASSIFICATION_COLLECTION)
            for category_record in all_categories:
                metadata = category_record.get("metadata", {})
                patterns_in_category = metadata.get("patterns", [])
                if pattern_id in patterns_in_category:
                    matching_categories.append(metadata)
            return matching_categories
        except Exception as e:
            self._logger.error(f"Error getting categories for pattern '{pattern_id}': {e}")
            return []