import unittest
from typing import Any, Optional
from unittest.mock import MagicMock, patch

# --- Dummy/Mock Classes for Testing ---
# These mocks simulate the behavior of ChromaDBConnector and PatternClassification
# to allow the tests to run without needing the actual implementations.


class DummyChromaDBConnector:
    """
    A simplified in-memory mock for ChromaDBConnector to simulate its basic operations
    for categories and pattern-category links.
    """

    def __init__(self):
        self.collections = {}  # Stores data for different collections

    def get_or_create_collection(self, name):
        """Simulates getting or creating a collection."""
        if name not in self.collections:
            self.collections[name] = {"documents": {}, "metadatas": {}, "ids": []}
        return self.collections[name]

    def add_documents(
        self,
        collection_name: str,
        documents: list[str],
        metadatas: list[dict[str, Any]],
        ids: list[str],
    ):
        """Simulates adding documents to a collection."""
        collection = self.get_or_create_collection(collection_name)
        for i, doc_id in enumerate(ids):
            if doc_id in collection["ids"]:
                # In a real ChromaDB, adding an existing ID might update or error.
                # For this mock, we'll just skip to prevent duplicates in our internal list.
                continue
            collection["documents"][doc_id] = documents[i]
            collection["metadatas"][doc_id] = metadatas[i]
            collection["ids"].append(doc_id)

    def get_documents(
        self,
        collection_name: str,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Simulates retrieving documents from a collection."""
        collection = self.get_or_create_collection(collection_name)
        results = []
        if ids:
            for doc_id in ids:
                if doc_id in collection["documents"]:
                    results.append(
                        {
                            "id": doc_id,
                            "document": collection["documents"][doc_id],
                            "metadata": collection["metadatas"][doc_id],
                        }
                    )
        elif where:
            # Simple 'where' clause simulation for metadata matching
            for doc_id in collection["ids"]:
                metadata = collection["metadatas"].get(doc_id, {})
                match = True
                for key, value in where.items():
                    if metadata.get(key) != value:
                        match = False
                        break
                if match:
                    results.append(
                        {
                            "id": doc_id,
                            "document": collection["documents"][doc_id],
                            "metadata": metadata,
                        }
                    )
        else:
            # Return all documents if no specific ids or where clause
            for doc_id in collection["ids"]:
                results.append(
                    {
                        "id": doc_id,
                        "document": collection["documents"][doc_id],
                        "metadata": collection["metadatas"][doc_id],
                    }
                )
        return results

    def update_documents(
        self,
        collection_name: str,
        ids: list[str],
        documents: list[str | None] | None = None,
        metadatas: list[dict[str, Any] | None] | None = None,
    ):
        """Simulates updating documents in a collection."""
        collection = self.get_or_create_collection(collection_name)
        for i, doc_id in enumerate(ids):
            if doc_id in collection["documents"]:
                if documents and documents[i] is not None:
                    collection["documents"][doc_id] = documents[i]
                if metadatas and metadatas[i] is not None:
                    collection["metadatas"][doc_id].update(metadatas[i])
            # If ID not found, do nothing (similar to how some DBs handle non-existent updates)

    def delete_documents(self, collection_name: str, ids: list[str]):
        """Simulates deleting documents from a collection."""
        collection = self.get_or_create_collection(collection_name)
        for doc_id in ids:
            if doc_id in collection["documents"]:
                del collection["documents"][doc_id]
                del collection["metadatas"][doc_id]
                if doc_id in collection["ids"]:
                    collection["ids"].remove(doc_id)

    def query_documents(
        self,
        collection_name: str,
        query_texts: Optional[list[str]] = None,
        query_embeddings: Optional[list[list[float]]] = None,
        n_results: int = 10,
        where: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Simplified query for testing, primarily uses 'where' clause."""
        return self.get_documents(collection_name, where=where)


class PatternClassification:
    """
    A mock implementation of the PatternClassification class based on the provided
    method signatures, using the DummyChromaDBConnector.
    """

    def __init__(self, db_connector: DummyChromaDBConnector):
        self.db_connector = db_connector
        self.categories_collection_name = "categories"
        self.pattern_category_links_collection_name = "pattern_category_links"

    def add_category(self, category_id: str, name: str, description: str = "") -> bool:
        """Adds a new category."""
        if self.db_connector.get_documents(
            self.categories_collection_name, ids=[category_id]
        ):
            return False  # Category already exists
        self.db_connector.add_documents(
            self.categories_collection_name,
            documents=[name],
            metadatas=[{"name": name, "description": description}],
            ids=[category_id],
        )
        return True

    def get_category(self, category_id: str) -> Optional[dict[str, Any]]:
        """Retrieves a category by its ID."""
        results = self.db_connector.get_documents(
            self.categories_collection_name, ids=[category_id]
        )
        if results:
            return {
                "id": results[0]["id"],
                "name": results[0]["document"],
                **results[0]["metadata"],
            }
        return None

    def update_category(
        self,
        category_id: str,
        new_name: Optional[str] = None,
        new_description: Optional[str] = None,
    ) -> bool:
        """Updates an existing category's name or description."""
        current_category = self.get_category(category_id)
        if not current_category:
            return False  # Category does not exist

        updated_metadata = {}
        updated_document = None
        if new_name is not None:
            updated_metadata["name"] = new_name
            updated_document = (
                new_name  # Document field often stores the primary name/text
            )
        if new_description is not None:
            updated_metadata["description"] = new_description

        if not updated_metadata and updated_document is None:
            return False  # No changes requested

        self.db_connector.update_documents(
            self.categories_collection_name,
            ids=[category_id],
            documents=[updated_document] if updated_document else [None],
            metadatas=[updated_metadata],
        )
        return True

    def delete_category(self, category_id: str) -> bool:
        """Deletes a category and all associated pattern links."""
        if not self.db_connector.get_documents(
            self.categories_collection_name, ids=[category_id]
        ):
            return False  # Category does not exist

        self.db_connector.delete_documents(
            self.categories_collection_name, ids=[category_id]
        )

        # Also delete all links associated with this category
        links_to_delete = self.db_connector.get_documents(
            self.pattern_category_links_collection_name,
            where={"category_id": category_id},
        )
        if links_to_delete:
            self.db_connector.delete_documents(
                self.pattern_category_links_collection_name,
                ids=[link["id"] for link in links_to_delete],
            )
        return True

    def assign_pattern_to_category(self, pattern_id: str, category_id: str) -> bool:
        """Assigns a pattern to a category."""
        if not self.get_category(category_id):
            return False  # Category must exist

        # Check if link already exists
        existing_links = self.db_connector.get_documents(
            self.pattern_category_links_collection_name,
            where={"pattern_id": pattern_id, "category_id": category_id},
        )
        if existing_links:
            return False  # Link already exists

        link_id = f"link_{pattern_id}_{category_id}"  # Unique ID for the link
        self.db_connector.add_documents(
            self.pattern_category_links_collection_name,
            documents=[f"Pattern {pattern_id} in Category {category_id}"],
            metadatas=[{"pattern_id": pattern_id, "category_id": category_id}],
            ids=[link_id],
        )
        return True

    def remove_pattern_from_category(self, pattern_id: str, category_id: str) -> bool:
        """Removes a pattern from a category."""
        links_to_delete = self.db_connector.get_documents(
            self.pattern_category_links_collection_name,
            where={"pattern_id": pattern_id, "category_id": category_id},
        )
        if not links_to_delete:
            return False  # Link does not exist

        self.db_connector.delete_documents(
            self.pattern_category_links_collection_name,
            ids=[link["id"] for link in links_to_delete],
        )
        return True

    def get_patterns_in_category(self, category_id: str) -> list[str]:
        """Retrieves all patterns assigned to a specific category."""
        links = self.db_connector.get_documents(
            self.pattern_category_links_collection_name,
            where={"category_id": category_id},
        )
        return sorted({link["metadata"]["pattern_id"] for link in links})

    def get_categories_for_pattern(self, pattern_id: str) -> list[str]:
        """Retrieves all categories a specific pattern is assigned to."""
        links = self.db_connector.get_documents(
            self.pattern_category_links_collection_name,
            where={"pattern_id": pattern_id},
        )
        return sorted({link["metadata"]["category_id"] for link in links})


# --- Test Class ---


class TestPatternClassification(unittest.TestCase):
    """
    Unit tests for the PatternClassification class.
    """

    def setUp(self):
        """Set up a fresh mock database and classifier for each test."""
        self.mock_db_connector = DummyChromaDBConnector()
        self.pattern_classifier = PatternClassification(self.mock_db_connector)

    def test_add_category(self):
        """Test adding new categories and handling duplicates."""
        # Test successful addition
        self.assertTrue(
            self.pattern_classifier.add_category(
                "cat1", "Category One", "Description for cat1"
            )
        )
        category = self.pattern_classifier.get_category("cat1")
        self.assertIsNotNone(category)
        self.assertEqual(category["name"], "Category One")
        self.assertEqual(category["description"], "Description for cat1")

        # Test adding a duplicate category (should fail)
        self.assertFalse(
            self.pattern_classifier.add_category("cat1", "Category One Duplicate")
        )
        category = self.pattern_classifier.get_category("cat1")
        self.assertEqual(category["name"], "Category One")  # Should not have changed

    def test_get_category(self):
        """Test retrieving existing and non-existent categories."""
        self.pattern_classifier.add_category("cat2", "Category Two")
        category = self.pattern_classifier.get_category("cat2")
        self.assertIsNotNone(category)
        self.assertEqual(category["id"], "cat2")
        self.assertEqual(category["name"], "Category Two")
        self.assertEqual(category["description"], "")

        # Test getting a non-existent category
        self.assertIsNone(self.pattern_classifier.get_category("non_existent_cat"))

    def test_update_category(self):
        """Test updating category details and handling non-existent categories."""
        self.pattern_classifier.add_category(
            "cat3", "Category Three", "Initial description"
        )

        # Test updating name and description
        self.assertTrue(
            self.pattern_classifier.update_category(
                "cat3", "Updated Category Three", "New description"
            )
        )
        category = self.pattern_classifier.get_category("cat3")
        self.assertEqual(category["name"], "Updated Category Three")
        self.assertEqual(category["description"], "New description")

        # Test updating only name
        self.assertTrue(
            self.pattern_classifier.update_category(
                "cat3", new_name="Only Name Changed"
            )
        )
        category = self.pattern_classifier.get_category("cat3")
        self.assertEqual(category["name"], "Only Name Changed")
        self.assertEqual(
            category["description"], "New description"
        )  # Description should remain

        # Test updating only description
        self.assertTrue(
            self.pattern_classifier.update_category(
                "cat3", new_description="Only Description Changed"
            )
        )
        category = self.pattern_classifier.get_category("cat3")
        self.assertEqual(category["name"], "Only Name Changed")  # Name should remain
        self.assertEqual(category["description"], "Only Description Changed")

        # Test updating non-existent category (should fail)
        self.assertFalse(
            self.pattern_classifier.update_category("non_existent_cat", "New Name")
        )

        # Test calling update with no actual changes requested (should fail)
        self.assertFalse(self.pattern_classifier.update_category("cat3"))

    def test_delete_category(self):
        """Test deleting categories and associated pattern links."""
        self.pattern_classifier.add_category("cat4", "Category Four")
        self.pattern_classifier.add_category("cat5", "Category Five")
        self.pattern_classifier.assign_pattern_to_category("patA", "cat4")
        self.pattern_classifier.assign_pattern_to_category("patB", "cat4")
        self.pattern_classifier.assign_pattern_to_category("patA", "cat5")

        # Test successful deletion of cat4
        self.assertTrue(self.pattern_classifier.delete_category("cat4"))
        self.assertIsNone(self.pattern_classifier.get_category("cat4"))
        self.assertEqual(
            self.pattern_classifier.get_patterns_in_category("cat4"), []
        )  # No patterns in deleted category
        self.assertEqual(
            self.pattern_classifier.get_categories_for_pattern("patA"), ["cat5"]
        )  # patA should only be in cat5 now

        # Test deleting non-existent category (should fail)
        self.assertFalse(self.pattern_classifier.delete_category("non_existent_cat"))

    def test_assign_pattern_to_category(self):
        """Test assigning patterns to categories and handling existing/non-existent cases."""
        self.pattern_classifier.add_category("cat6", "Category Six")

        # Test successful assignment
        self.assertTrue(
            self.pattern_classifier.assign_pattern_to_category("pat1", "cat6")
        )
        self.assertEqual(
            self.pattern_classifier.get_patterns_in_category("cat6"), ["pat1"]
        )
        self.assertEqual(
            self.pattern_classifier.get_categories_for_pattern("pat1"), ["cat6"]
        )

        # Test assigning same pattern to same category (should fail as it's already assigned)
        self.assertFalse(
            self.pattern_classifier.assign_pattern_to_category("pat1", "cat6")
        )

        # Test assigning to non-existent category (should fail)
        self.assertFalse(
            self.pattern_classifier.assign_pattern_to_category(
                "pat2", "non_existent_cat"
            )
        )
        self.assertEqual(
            self.pattern_classifier.get_patterns_in_category("non_existent_cat"), []
        )

        # Assign another pattern to the same category
        self.assertTrue(
            self.pattern_classifier.assign_pattern_to_category("pat2", "cat6")
        )
        self.assertEqual(
            self.pattern_classifier.get_patterns_in_category("cat6"), ["pat1", "pat2"]
        )

        # Assign same pattern to another category
        self.pattern_classifier.add_category("cat7", "Category Seven")
        self.assertTrue(
            self.pattern_classifier.assign_pattern_to_category("pat1", "cat7")
        )
        self.assertEqual(
            self.pattern_classifier.get_categories_for_pattern("pat1"), ["cat6", "cat7"]
        )

    def test_remove_pattern_from_category(self):
        """Test removing patterns from categories and handling non-existent links."""
        self.pattern_classifier.add_category("cat8", "Category Eight")
        self.pattern_classifier.add_category("cat9", "Category Nine")
        self.pattern_classifier.assign_pattern_to_category("pat3", "cat8")
        self.pattern_classifier.assign_pattern_to_category("pat3", "cat9")
        self.pattern_classifier.assign_pattern_to_category("pat4", "cat8")

        # Test successful removal
        self.assertTrue(
            self.pattern_classifier.remove_pattern_from_category("pat3", "cat8")
        )
        self.assertEqual(
            self.pattern_classifier.get_patterns_in_category("cat8"), ["pat4"]
        )
        self.assertEqual(
            self.pattern_classifier.get_categories_for_pattern("pat3"), ["cat9"]
        )

        # Test removing non-existent link (already removed or never existed)
        self.assertFalse(
            self.pattern_classifier.remove_pattern_from_category("pat3", "cat8")
        )  # Already removed
        self.assertFalse(
            self.pattern_classifier.remove_pattern_from_category("patX", "cat8")
        )  # Non-existent pattern
        self.assertFalse(
            self.pattern_classifier.remove_pattern_from_category("pat3", "catX")
        )  # Non-existent category

        # Remove last link for pat3
        self.assertTrue(
            self.pattern_classifier.remove_pattern_from_category("pat3", "cat9")
        )
        self.assertEqual(self.pattern_classifier.get_categories_for_pattern("pat3"), [])

    def test_get_patterns_in_category(self):
        """Test retrieving patterns for a given category."""
        self.pattern_classifier.add_category("cat10", "Category Ten")
        self.pattern_classifier.assign_pattern_to_category("patA", "cat10")
        self.pattern_classifier.assign_pattern_to_category("patC", "cat10")
        self.pattern_classifier.assign_pattern_to_category("patB", "cat10")

        # Test retrieving patterns (should be sorted)
        patterns = self.pattern_classifier.get_patterns_in_category("cat10")
        self.assertEqual(patterns, ["patA", "patB", "patC"])

        # Test category with no patterns
        self.pattern_classifier.add_category("cat11", "Category Eleven")
        self.assertEqual(self.pattern_classifier.get_patterns_in_category("cat11"), [])

        # Test non-existent category
        self.assertEqual(
            self.pattern_classifier.get_patterns_in_category("non_existent_cat"), []
        )

    def test_get_categories_for_pattern(self):
        """Test retrieving categories for a given pattern."""
        self.pattern_classifier.add_category("cat12", "Category Twelve")
        self.pattern_classifier.add_category("cat13", "Category Thirteen")
        self.pattern_classifier.add_category("cat14", "Category Fourteen")

        self.pattern_classifier.assign_pattern_to_category("patX", "cat12")
        self.pattern_classifier.assign_pattern_to_category("patX", "cat14")
        self.pattern_classifier.assign_pattern_to_category("patY", "cat12")

        # Test retrieving categories for a pattern (should be sorted)
        categories = self.pattern_classifier.get_categories_for_pattern("patX")
        self.assertEqual(categories, ["cat12", "cat14"])

        # Test pattern with no categories
        self.assertEqual(self.pattern_classifier.get_categories_for_pattern("patZ"), [])

        # Test pattern with only one category
        categories_y = self.pattern_classifier.get_categories_for_pattern("patY")
        self.assertEqual(categories_y, ["cat12"])
