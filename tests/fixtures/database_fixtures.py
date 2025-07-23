"""
Database/storage fixtures for UCKN tests.

Provides:
- ChromaDB mock connector with realistic test data
- PostgreSQL mock connector
- UnifiedDatabase mock connector
- Storage schema standardization
- Performance dataset fixtures
- Database state management helpers
"""

import copy
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import pytest


# Mock classes for connectors
class DummyChromaDBConnector:
    """
    A mock ChromaDBConnector for testing.
    Includes a close() method for resource cleanup.
    """
    def __init__(self):
        self.collections = {
            "code_patterns": [],
            "error_solutions": []
        }
        self.added_docs = []

    def is_available(self):
        return True

    def close(self):
        # Dummy close for interface compatibility
        self.collections = {}
        self.added_docs = []

    def add_document(self, collection_name, doc_id, document, embedding, metadata):
        doc = {
            "id": doc_id,
            "document": document,
            "embedding": embedding,
            "metadata": metadata
        }
        self.collections[collection_name].append(doc)
        self.added_docs.append(doc)
        return True

    def get_document(self, collection_name, doc_id):
        for doc in self.collections[collection_name]:
            if doc["id"] == doc_id:
                return doc
        return None

    def update_document(self, collection_name, doc_id, document=None, embedding=None, metadata=None):
        for doc in self.collections[collection_name]:
            if doc["id"] == doc_id:
                if document is not None:
                    doc["document"] = document
                if embedding is not None:
                    doc["embedding"] = embedding
                if metadata is not None:
                    doc["metadata"].update(metadata) # Merge metadata
                return True
        return False

    def delete_document(self, collection_name, doc_id):
        initial_len = len(self.collections[collection_name])
        self.collections[collection_name] = [doc for doc in self.collections[collection_name] if doc["id"] != doc_id]
        return len(self.collections[collection_name]) < initial_len

    def search_documents(self, collection_name, query_embedding, n_results=10, min_similarity=0.7, where_clause=None):
        # Simple mock search: return all documents, filter by where_clause if present
        # and assign a dummy similarity score.
        results = []
        for doc in self.collections[collection_name]:
            match = True
            if where_clause:
                for key, value in where_clause.items():
                    if doc["metadata"].get(key) != value:
                        match = False
                        break
            if match:
                # Dummy similarity, higher for earlier docs
                similarity = 1.0 - (len(results) * 0.05) # Decreasing similarity
                if similarity >= min_similarity:
                    results.append({
                        "id": doc["id"],
                        "document": doc["document"],
                        "metadata": doc["metadata"],
                        "similarity_score": similarity
                    })
            if len(results) >= n_results:
                break
        return results

    def count_documents(self, collection_name):
        return len(self.collections[collection_name])

    def reset_db(self):
        for k in self.collections:
            self.collections[k] = []
        self.added_docs = []
        return True

class DummyPostgreSQLConnector:
    """
    A mock PostgreSQLConnector for testing.
    Simulates basic CRUD and relationship operations in memory.
    """
    def __init__(self):
        self.tables = {
            "projects": {},
            "patterns": {},
            "error_solutions": {},
            "pattern_categories": {},
            "pattern_category_links": {}, # Stores tuples (pattern_id, category_id)
            "team_access": {},
            "compatibility_matrix": {}
        }
        self._logger = logging.getLogger(__name__)

    def is_available(self):
        return True

    def add_record(self, model_class: Any, data: dict[str, Any]) -> str | None:
        table_name = model_class.__tablename__
        record_id = data.get("id", str(uuid.uuid4()))
        record = data.copy()
        record["id"] = record_id
        record["created_at"] = record.get("created_at", datetime.utcnow())
        record["updated_at"] = record.get("updated_at", datetime.utcnow())
        self.tables[table_name][record_id] = record
        self._logger.debug(f"Dummy PG: Added {table_name} {record_id}")
        return record_id

    def get_record(self, model_class: Any, record_id: str) -> dict[str, Any] | None:
        table_name = model_class.__tablename__
        return self.tables[table_name].get(record_id)

    def update_record(self, model_class: Any, record_id: str, updates: dict[str, Any]) -> bool:
        table_name = model_class.__tablename__
        record = self.tables[table_name].get(record_id)
        if record:
            record.update(updates)
            record["updated_at"] = datetime.utcnow()
            self._logger.debug(f"Dummy PG: Updated {table_name} {record_id}")
            return True
        return False

    def delete_record(self, model_class: Any, record_id: str) -> bool:
        table_name = model_class.__tablename__
        if record_id in self.tables[table_name]:
            del self.tables[table_name][record_id]
            self._logger.debug(f"Dummy PG: Deleted {table_name} {record_id}")
            # Simulate cascading deletes for links
            if table_name == "patterns":
                # Remove links where this pattern is involved
                self.tables["pattern_category_links"] = {
                    k: v for k, v in self.tables["pattern_category_links"].items()
                    if v[0] != record_id
                }
            elif table_name == "pattern_categories":
                # Remove links where this category is involved
                self.tables["pattern_category_links"] = {
                    k: v for k, v in self.tables["pattern_category_links"].items()
                    if v[1] != record_id
                }
            return True
        return False

    def get_all_records(self, model_class: Any, limit: int | None = None) -> list[dict[str, Any]]:
        table_name = model_class.__tablename__
        records = list(self.tables[table_name].values())
        return records[:limit] if limit else records

    def filter_records(self, model_class: Any, filters: dict[str, Any], limit: int | None = None) -> list[dict[str, Any]]:
        table_name = model_class.__tablename__
        results = []
        for record in self.tables[table_name].values():
            match = True
            for key, value in filters.items():
                if record.get(key) != value:
                    match = False
                    break
            if match:
                results.append(record)
        return results[:limit] if limit else results

    def add_pattern_to_category(self, pattern_id: str, category_id: str) -> bool:
        link_id = f"{pattern_id}-{category_id}"
        if link_id in self.tables["pattern_category_links"]:
            self._logger.debug(f"Dummy PG: Link between pattern {pattern_id} and category {category_id} already exists.")
            return True # Idempotent
        self.tables["pattern_category_links"][link_id] = (pattern_id, category_id)
        self._logger.debug(f"Dummy PG: Linked pattern {pattern_id} to category {category_id}")
        return True

    def remove_pattern_from_category(self, pattern_id: str, category_id: str) -> bool:
        link_id = f"{pattern_id}-{category_id}"
        if link_id in self.tables["pattern_category_links"]:
            del self.tables["pattern_category_links"][link_id]
            self._logger.debug(f"Dummy PG: Unlinked pattern {pattern_id} from category {category_id}")
            return True
        self._logger.debug(f"Dummy PG: Link between pattern {pattern_id} and category {category_id} not found for removal.")
        return True # Idempotent: if not found, it's effectively removed

    def get_patterns_in_category(self, category_id: str) -> list[str]:
        return [link[0] for link in self.tables["pattern_category_links"].values() if link[1] == category_id]

    def get_categories_for_pattern(self, pattern_id: str) -> list[dict[str, Any]]:
        category_ids = [link[1] for link in self.tables["pattern_category_links"].values() if link[0] == pattern_id]
        # Need to mock the model classes for get_record to work with them
        mock_pattern_category_model = type("PatternCategory", (object,), {"__tablename__": "pattern_categories"})
        return [self.get_record(mock_pattern_category_model, cid) for cid in category_ids if self.get_record(mock_pattern_category_model, cid)]

    def reset_db(self) -> bool:
        for table_name in self.tables:
            self.tables[table_name] = {}
        self._logger.debug("Dummy PG: Database reset.")
        return True


# Mock SQLAlchemy Base and Models for DummyPostgreSQLConnector
# This is a workaround to allow DummyPostgreSQLConnector to accept `model_class` arguments
# that resemble SQLAlchemy models, without actually importing SQLAlchemy models directly
# into the fixture file, which might cause circular dependencies or real DB connections.
class MockSQLAlchemyModel:
    def __init__(self, tablename):
        self.__tablename__ = tablename

# Create mock model instances for use in DummyPostgreSQLConnector
MockProject = MockSQLAlchemyModel("projects")
MockPattern = MockSQLAlchemyModel("patterns")
MockErrorSolution = MockSQLAlchemyModel("error_solutions")
MockPatternCategory = MockSQLAlchemyModel("pattern_categories")
MockPatternCategoryLink = MockSQLAlchemyModel("pattern_category_links")
MockTeamAccess = MockSQLAlchemyModel("team_access")
MockCompatibilityMatrix = MockSQLAlchemyModel("compatibility_matrix")


class DummyUnifiedDatabase:
    """
    A mock UnifiedDatabase for testing, combining dummy Chroma and PostgreSQL.
    """
    def __init__(self):
        self.pg_connector = DummyPostgreSQLConnector()
        self.chroma_connector = DummyChromaDBConnector()
        self._logger = logging.getLogger(__name__)

    def is_available(self):
        return self.pg_connector.is_available() and self.chroma_connector.is_available()

    def reset_db(self):
        return self.pg_connector.reset_db() and self.chroma_connector.reset_db()

    # Simplified mock implementations for key methods
    def add_pattern(self, document_text: str, embedding: list[float], metadata: dict[str, Any], pattern_id: str | None = None, project_id: str | None = None) -> str | None:
        pattern_id = pattern_id or str(uuid.uuid4())
        pg_metadata = metadata.copy()
        pg_metadata.update({"id": pattern_id, "project_id": project_id, "document_text": document_text})
        # Populate specific columns for PG mock
        pg_metadata["technology_stack"] = metadata.get("technology_stack")
        pg_metadata["pattern_type"] = metadata.get("pattern_type")
        pg_metadata["success_rate"] = metadata.get("success_rate")

        pg_success = self.pg_connector.add_record(MockPattern, pg_metadata)
        if not pg_success: return None
        chroma_success = self.chroma_connector.add_document("code_patterns", pattern_id, document_text, embedding, metadata)
        if not chroma_success:
            self.pg_connector.delete_record(MockPattern, pattern_id)
            return None
        return pattern_id

    def get_pattern(self, pattern_id: str) -> dict[str, Any] | None:
        pg_data = self.pg_connector.get_record(MockPattern, pattern_id)
        if not pg_data: return None
        chroma_data = self.chroma_connector.get_document("code_patterns", pattern_id)

        combined = pg_data.copy()
        if chroma_data:
            combined["document"] = chroma_data["document"]
            combined["embedding"] = chroma_data["embedding"]
            # Use PG's metadata_json as source of truth for metadata
            combined["metadata"] = pg_data.get("metadata_json", {})
        else:
            combined["document"] = pg_data["document_text"]
            combined["embedding"] = None
            combined["metadata"] = pg_data.get("metadata_json", {})
        return combined

    def update_pattern(self, pattern_id: str, document_text: str | None = None, embedding: list[float] | None = None, metadata: dict[str, Any] | None = None, project_id: str | None = None) -> bool:
        pg_updates = {"updated_at": datetime.utcnow()}
        if document_text is not None: pg_updates["document_text"] = document_text
        if metadata is not None:
            pg_updates["metadata_json"] = metadata
            if "technology_stack" in metadata: pg_updates["technology_stack"] = metadata["technology_stack"]
            if "pattern_type" in metadata: pg_updates["pattern_type"] = metadata["pattern_type"]
            if "success_rate" in metadata: pg_updates["success_rate"] = metadata["success_rate"]
        if project_id is not None: pg_updates["project_id"] = project_id

        pg_success = self.pg_connector.update_record(MockPattern, pattern_id, pg_updates)
        if not pg_success: return False

        chroma_success = self.chroma_connector.update_document("code_patterns", pattern_id, document_text, embedding, metadata)
        return chroma_success

    def delete_pattern(self, pattern_id: str) -> bool:
        pg_success = self.pg_connector.delete_record(MockPattern, pattern_id)
        chroma_success = self.chroma_connector.delete_document("code_patterns", pattern_id)
        return pg_success and chroma_success

    def search_patterns(self, query_embedding: list[float], n_results: int = 10, min_similarity: float = 0.7, metadata_filter: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        chroma_results = self.chroma_connector.search_documents("code_patterns", query_embedding, n_results, min_similarity, metadata_filter)
        final_results = []
        for res in chroma_results:
            pg_data = self.pg_connector.get_record(MockPattern, res["id"])
            if pg_data:
                combined_res = {
                    "id": res["id"],
                    "document": res["document"],
                    "metadata": pg_data.get("metadata_json", {}),
                    "similarity_score": res["similarity_score"],
                    "project_id": pg_data.get("project_id"),
                    "created_at": pg_data.get("created_at"),
                    "updated_at": pg_data.get("updated_at"),
                }
                final_results.append(combined_res)
        return final_results

    # Add other unified_db methods as needed for specific tests
    def add_project(self, name: str, description: str | None = None, project_id: str | None = None) -> str | None:
        return self.pg_connector.add_record(MockProject, {"id": project_id or str(uuid.uuid4()), "name": name, "description": description})

    def get_project(self, project_id: str) -> dict[str, Any] | None:
        return self.pg_connector.get_record(MockProject, project_id)

    def update_project(self, project_id: str, updates: dict[str, Any]) -> bool:
        return self.pg_connector.update_record(MockProject, project_id, updates)

    def delete_project(self, project_id: str) -> bool:
        return self.pg_connector.delete_record(MockProject, project_id)

    def get_all_projects(self) -> list[dict[str, Any]]:
        return self.pg_connector.get_all_records(MockProject)

    def add_category(self, name: str, description: str = "", category_id: str | None = None) -> str | None:
        return self.pg_connector.add_record(MockPatternCategory, {"id": category_id or str(uuid.uuid4()), "name": name, "description": description})

    def get_category(self, category_id: str) -> dict[str, Any] | None:
        return self.pg_connector.get_record(MockPatternCategory, category_id)

    def update_category(self, category_id: str, updates: dict[str, Any]) -> bool:
        return self.pg_connector.update_record(MockPatternCategory, category_id, updates)

    def delete_category(self, category_id: str) -> bool:
        return self.pg_connector.delete_record(MockPatternCategory, category_id)

    def assign_pattern_to_category(self, pattern_id: str, category_id: str) -> bool:
        # In the mock, we don't need to check existence of pattern/category, just link
        return self.pg_connector.add_pattern_to_category(pattern_id, category_id)

    def remove_pattern_from_category(self, pattern_id: str, category_id: str) -> bool:
        return self.pg_connector.remove_pattern_from_category(pattern_id, category_id)

    def get_patterns_by_category(self, category_id: str) -> list[str]:
        return self.pg_connector.get_patterns_in_category(category_id)

    def get_categories_for_pattern(self, pattern_id: str) -> list[dict[str, Any]]:
        return self.pg_connector.get_categories_for_pattern(pattern_id)

    def add_error_solution(self, document_text: str, embedding: list[float], metadata: dict[str, Any], solution_id: str | None = None, project_id: str | None = None) -> str | None:
        solution_id = solution_id or str(uuid.uuid4())
        pg_metadata = metadata.copy()
        pg_metadata.update({"id": solution_id, "project_id": project_id, "document_text": document_text})
        # Populate specific columns for PG mock
        pg_metadata["error_category"] = metadata.get("error_category")
        pg_metadata["resolution_steps"] = metadata.get("resolution_steps")
        pg_metadata["avg_resolution_time"] = metadata.get("avg_resolution_time")

        pg_success = self.pg_connector.add_record(MockErrorSolution, pg_metadata)
        if not pg_success: return None
        chroma_success = self.chroma_connector.add_document("error_solutions", solution_id, document_text, embedding, metadata)
        if not chroma_success:
            self.pg_connector.delete_record(MockErrorSolution, solution_id)
            return None
        return solution_id

    def get_error_solution(self, solution_id: str) -> dict[str, Any] | None:
        pg_data = self.pg_connector.get_record(MockErrorSolution, solution_id)
        if not pg_data: return None
        chroma_data = self.chroma_connector.get_document("error_solutions", solution_id)

        combined = pg_data.copy()
        if chroma_data:
            combined["document"] = chroma_data["document"]
            combined["embedding"] = chroma_data["embedding"]
            combined["metadata"] = pg_data.get("metadata_json", {})
        else:
            combined["document"] = pg_data["document_text"]
            combined["embedding"] = None
            combined["metadata"] = pg_data.get("metadata_json", {})
        return combined

    def search_error_solutions(self, query_embedding: list[float], n_results: int = 10, min_similarity: float = 0.7, metadata_filter: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        chroma_results = self.chroma_connector.search_documents("error_solutions", query_embedding, n_results, min_similarity, metadata_filter)
        final_results = []
        for res in chroma_results:
            pg_data = self.pg_connector.get_record(MockErrorSolution, res["id"])
            if pg_data:
                combined_res = {
                    "id": res["id"],
                    "document": res["document"],
                    "metadata": pg_data.get("metadata_json", {}),
                    "similarity_score": res["similarity_score"],
                    "project_id": pg_data.get("project_id"),
                    "created_at": pg_data.get("created_at"),
                    "updated_at": pg_data.get("updated_at"),
                }
                final_results.append(combined_res)
        return final_results

    def add_team_access(self, user_id: str, project_id: str, role: str, access_id: str | None = None) -> str | None:
        return self.pg_connector.add_record(MockTeamAccess, {"id": access_id or str(uuid.uuid4()), "user_id": user_id, "project_id": project_id, "role": role})

    def get_team_access(self, access_id: str) -> dict[str, Any] | None:
        return self.pg_connector.get_record(MockTeamAccess, access_id)

    def update_team_access(self, access_id: str, updates: dict[str, Any]) -> bool:
        return self.pg_connector.update_record(MockTeamAccess, access_id, updates)

    def delete_team_access(self, access_id: str) -> bool:
        return self.pg_connector.delete_record(MockTeamAccess, access_id)

    def get_team_access_for_project(self, project_id: str) -> list[dict[str, Any]]:
        return self.pg_connector.filter_records(MockTeamAccess, {"project_id": project_id})

    def add_compatibility_entry(self, source_tech: str, target_tech: str, compatibility_score: float, notes: str | None = None, entry_id: str | None = None) -> str | None:
        return self.pg_connector.add_record(MockCompatibilityMatrix, {"id": entry_id or str(uuid.uuid4()), "source_tech": source_tech, "target_tech": target_tech, "compatibility_score": compatibility_score, "notes": notes})

    def get_compatibility_entry(self, entry_id: str) -> dict[str, Any] | None:
        return self.pg_connector.get_record(MockCompatibilityMatrix, entry_id)

    def update_compatibility_entry(self, entry_id: str, updates: dict[str, Any]) -> bool:
        return self.pg_connector.update_record(MockCompatibilityMatrix, entry_id, updates)

    def delete_compatibility_entry(self, entry_id: str) -> bool:
        return self.pg_connector.delete_record(MockCompatibilityMatrix, entry_id)

    def search_compatibility_entries(self, source_tech: str | None = None, target_tech: str | None = None, min_score: float | None = None, max_score: float | None = None) -> list[dict[str, Any]]:
        filters = {}
        if source_tech: filters["source_tech"] = source_tech
        if target_tech: filters["target_tech"] = target_tech
        results = self.pg_connector.filter_records(MockCompatibilityMatrix, filters)

        if min_score is not None or max_score is not None:
            filtered_results = []
            for res in results:
                score = res.get("compatibility_score")
                if score is not None:
                    if (min_score is None or score >= min_score) and \
                       (max_score is None or score <= max_score):
                        filtered_results.append(res)
            return filtered_results
        return results


# Pytest fixtures
@pytest.fixture
def dummy_chromadb_connector():
    """
    Returns a dummy ChromaDBConnector for isolated storage testing.
    Ensures cleanup after test.
    """
    connector = DummyChromaDBConnector()
    yield connector
    try:
        connector.close()
    except Exception:
        pass

@pytest.fixture
def dummy_postgresql_connector():
    """
    Returns a dummy PostgreSQLConnector for isolated storage testing.
    """
    return DummyPostgreSQLConnector()

@pytest.fixture
def dummy_unified_database():
    """
    Returns a dummy UnifiedDatabase for isolated testing of the unified layer.
    Ensures cleanup after test.
    """
    db = DummyUnifiedDatabase()
    yield db
    try:
        db.chroma_connector.close()
    except Exception:
        pass

@pytest.fixture
def performance_dataset():
    """
    Returns a large dataset for performance and scalability testing.
    """
    base_doc = {
        "id": "perf-doc-{}",
        "document": "Performance test document {}",
        "embedding": [0.1] * 384,
        "metadata": {"test": True}
    }
    return [
        {
            "id": base_doc["id"].format(i),
            "document": base_doc["document"].format(i),
            "embedding": [float(i % 10)] * 384,
            "metadata": {"test": True, "index": i}
        }
        for i in range(1000)
    ]

@pytest.fixture
def db_state_manager(dummy_chromadb_connector, dummy_postgresql_connector):
    """
    Helper for managing database state across test scenarios for both dummy connectors.
    """
    class DBStateManager:
        def __init__(self, chroma_connector, pg_connector):
            self.chroma_connector = chroma_connector
            self.pg_connector = pg_connector
            self.chroma_snapshots = []
            self.pg_snapshots = []

        def snapshot(self):
            self.chroma_snapshots.append(copy.deepcopy(self.chroma_connector.collections))
            self.pg_snapshots.append(copy.deepcopy(self.pg_connector.tables))

        def restore(self):
            if self.chroma_snapshots:
                self.chroma_connector.collections = self.chroma_snapshots.pop()
            if self.pg_snapshots:
                self.pg_connector.tables = self.pg_snapshots.pop()
    return DBStateManager(dummy_chromadb_connector, dummy_postgresql_connector)
