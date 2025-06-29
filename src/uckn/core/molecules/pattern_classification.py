"""
UCKN Pattern Classification Molecule
Handles management of pattern categories and their assignments.
"""

from typing import Dict, List, Optional, Any
import uuid
import logging

from ...storage import UnifiedDatabase # Changed from ChromaDBConnector

class PatternClassification:
    """
    Manages pattern categories and the assignment of patterns to categories
    using the Unified Database.
    """

    def __init__(self, unified_db: UnifiedDatabase):
        self.unified_db = unified_db # Now uses UnifiedDatabase
        self._logger = logging.getLogger(__name__)

    def add_category(self, name: str, description: str = "", category_id: Optional[str] = None) -> Optional[str]:
        """
        Adds a new pattern category to the database.

        Args:
            name: The name of the category. Must be unique.
            description: A description for the category.
            category_id: Optional, a specific ID for the category. If None, a UUID is generated.

        Returns:
            The ID of the newly created category, or None if creation failed.
        """
        if not self.unified_db.is_available():
            self._logger.error("Unified Database not available, cannot add category.")
            return None
        
        category_id = category_id or str(uuid.uuid4())
        
        # UnifiedDatabase handles adding to PostgreSQL
        success = self.unified_db.add_category(name=name, description=description, category_id=category_id)
        return category_id if success else None

    def get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a pattern category by its ID.

        Args:
            category_id: The ID of the category to retrieve.

        Returns:
            A dictionary containing category details, or None if not found.
        """
        if not self.unified_db.is_available():
            self._logger.warning("Unified Database not available, cannot retrieve category.")
            return None
        # UnifiedDatabase handles getting from PostgreSQL
        return self.unified_db.get_category(category_id)

    def update_category(self, category_id: str, name: Optional[str] = None, description: Optional[str] = None) -> bool:
        """
        Updates an existing pattern category.

        Args:
            category_id: The ID of the category to update.
            name: New name for the category (optional).
            description: New description for the category (optional).

        Returns:
            True if the category was updated successfully, False otherwise.
        """
        if not self.unified_db.is_available():
            self._logger.warning("Unified Database not available, cannot update category.")
            return False
        
        updates = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        
        if not updates:
            self._logger.info(f"No updates provided for category {category_id}.")
            return False

        # UnifiedDatabase handles updating in PostgreSQL
        return self.unified_db.update_category(category_id, updates)

    def delete_category(self, category_id: str) -> bool:
        """
        Deletes a pattern category and all its associated pattern links.

        Args:
            category_id: The ID of the category to delete.

        Returns:
            True if the category was deleted successfully, False otherwise.
        """
        if not self.unified_db.is_available():
            self._logger.warning("Unified Database not available, cannot delete category.")
            return False
        # UnifiedDatabase handles deleting from PostgreSQL (including cascading links)
        return self.unified_db.delete_category(category_id)

    def assign_pattern_to_category(self, pattern_id: str, category_id: str) -> bool:
        """
        Assigns an existing pattern to an existing category.

        Args:
            pattern_id: The ID of the pattern.
            category_id: The ID of the category.

        Returns:
            True if the assignment was successful, False otherwise.
        """
        if not self.unified_db.is_available():
            self._logger.warning("Unified Database not available, cannot assign pattern to category.")
            return False
        
        # Check if pattern and category exist (optional, but good for data integrity)
        # These checks are now done via the unified_db's get methods, which in turn
        # query PostgreSQL.
        if not self.unified_db.get_pattern(pattern_id):
            self._logger.error(f"Pattern with ID '{pattern_id}' not found.")
            return False
        if not self.unified_db.get_category(category_id):
            self._logger.error(f"Category with ID '{category_id}' not found.")
            return False

        # UnifiedDatabase handles linking in PostgreSQL
        return self.unified_db.assign_pattern_to_category(pattern_id, category_id)

    def remove_pattern_from_category(self, pattern_id: str, category_id: str) -> bool:
        """
        Removes a pattern from a specific category.

        Args:
            pattern_id: The ID of the pattern.
            category_id: The ID of the category.

        Returns:
            True if the removal was successful, False otherwise.
        """
        if not self.unified_db.is_available():
            self._logger.warning("Unified Database not available, cannot remove pattern from category.")
            return False
        # UnifiedDatabase handles removing link in PostgreSQL
        return self.unified_db.remove_pattern_from_category(pattern_id, category_id)

    def get_patterns_in_category(self, category_id: str) -> List[str]:
        """
        Retrieves a list of pattern IDs belonging to a specific category.

        Args:
            category_id: The ID of the category.

        Returns:
            A list of pattern IDs.
        """
        if not self.unified_db.is_available():
            self._logger.warning("Unified Database not available, cannot get patterns in category.")
            return []
        # UnifiedDatabase handles querying links in PostgreSQL
        return self.unified_db.get_patterns_by_category(category_id)

    def get_categories_for_pattern(self, pattern_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves a list of categories assigned to a specific pattern.

        Args:
            pattern_id: The ID of the pattern.

        Returns:
            A list of dictionaries, each representing a category.
        """
        if not self.unified_db.is_available():
            self._logger.warning("Unified Database not available, cannot get categories for pattern.")
            return []
        # UnifiedDatabase handles querying links and categories in PostgreSQL
        return self.unified_db.get_pattern_categories(pattern_id)
