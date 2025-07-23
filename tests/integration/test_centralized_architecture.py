import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

import pytest

from src.uckn.core.organisms.knowledge_manager import KnowledgeManager
from src.uckn.storage.chromadb_connector import ChromaDBConnector
from src.uckn.storage.postgresql_connector import (
    Base,
    ErrorSolution,
    Pattern,
    PatternCategory,
    PatternCategoryLink,
    PostgreSQLConnector,
    Project,
)
from src.uckn.storage.unified_database import UnifiedDatabase

# Use a temporary directory for ChromaDB and an in-memory SQLite for PostgreSQL
# For true integration testing, a Dockerized PostgreSQL might be preferred,
# but for CI/CD simplicity, in-memory SQLite is often used for the PG part.
# Note: SQLite's JSON support is limited compared to PostgreSQL's JSONB.
# For full JSONB testing, a real PostgreSQL instance would be needed.
TEST_PG_DB_URL = "sqlite:///:memory:"
TEST_CHROMA_DIR = ".uckn_test_knowledge_integration"

@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown_dbs():
    """
    Sets up in-memory SQLite and temporary ChromaDB for the module,
    and cleans them up afterwards.
    """
    # Setup PostgreSQL (SQLite in-memory)
    pg_connector = PostgreSQLConnector(db_url=TEST_PG_DB_URL)
    Base.metadata.create_all(pg_connector.engine)

    # Setup ChromaDB (temporary directory)
    chroma_path = Path(TEST_CHROMA_DIR)
    if chroma_path.exists():
        shutil.rmtree(chroma_path)
    chroma_path.mkdir(parents=True, exist_ok=True)

    yield # Run tests

    # Teardown PostgreSQL
    Base.metadata.drop_all(pg_connector.engine)
    pg_connector.engine.dispose()

    # Teardown ChromaDB
    if chroma_path.exists():
        shutil.rmtree(chroma_path)

@pytest.fixture(scope="function")
def knowledge_manager_instance():
    """Provides a KnowledgeManager instance for integration tests."""
    # Ensure a clean state for each test function
    pg_connector = PostgreSQLConnector(db_url=TEST_PG_DB_URL)
    Base.metadata.drop_all(pg_connector.engine)
    Base.metadata.create_all(pg_connector.engine)

    chroma_path = Path(TEST_CHROMA_DIR)
    if chroma_path.exists():
        shutil.rmtree(chroma_path)
    chroma_path.mkdir(parents=True, exist_ok=True)

    # Initialize KnowledgeManager with test paths/URLs
    km = KnowledgeManager(knowledge_dir=TEST_CHROMA_DIR, pg_db_url=TEST_PG_DB_URL)

    # Ensure semantic search is mocked or available for tests that need embeddings
    # For integration tests, we might mock the actual embedding generation
    # to avoid downloading models and speed up tests.
    km.semantic_search.is_available = lambda: True
    km.semantic_search.encode = lambda text: [float(ord(c) % 10) / 10.0 for c in text[:384].ljust(384, '0')] # Simple mock embedding

    yield km

    # Clean up after each test function
    pg_connector = PostgreSQLConnector(db_url=TEST_PG_DB_URL)
    Base.metadata.drop_all(pg_connector.engine)
    Base.metadata.create_all(pg_connector.engine) # Recreate empty tables for next test

    chroma_path = Path(TEST_CHROMA_DIR)
    if chroma_path.exists():
        shutil.rmtree(chroma_path)
    chroma_path.mkdir(parents=True, exist_ok=True)


@pytest.mark.integration
def test_knowledge_manager_full_lifecycle_pattern(knowledge_manager_instance):
    km = knowledge_manager_instance
    assert km.get_health_status()["unified_db_available"]
    assert km.get_health_status()["semantic_search_available"]

    # 1. Add a Project
    project_id = km.add_project(name="My Test Project", description="A project for integration testing.")
    assert project_id is not None
    retrieved_project = km.get_project(project_id)
    assert retrieved_project["name"] == "My Test Project"

    # 2. Add a Pattern
    pattern_data = {
        "document": "This is a test code pattern for Python.",
        "metadata": {
            "technology_stack": "python,django",
            "pattern_type": "Architectural",
            "success_rate": 0.98,
            "source": "internal"
        },
        "project_id": project_id
    }
    pattern_id = km.add_pattern(pattern_data)
    assert pattern_id is not None

    # 3. Retrieve the Pattern
    retrieved_pattern = km.get_pattern(pattern_id)
    assert retrieved_pattern is not None
    assert retrieved_pattern["id"] == pattern_id
    assert retrieved_pattern["document"] == "This is a test code pattern for Python."
    assert retrieved_pattern["metadata"]["technology_stack"] == "python,django"
    assert retrieved_pattern["project_id"] == project_id
    assert "embedding" in retrieved_pattern and retrieved_pattern["embedding"] is not None

    # 4. Update the Pattern
    updated_doc = "This is an updated test code pattern for Python."
    updated_metadata = {"success_rate": 0.99, "new_field": "value"}
    updated = km.update_pattern(pattern_id, {"document": updated_doc, "metadata": updated_metadata})
    assert updated

    retrieved_updated_pattern = km.get_pattern(pattern_id)
    assert retrieved_updated_pattern["document"] == updated_doc
    assert retrieved_updated_pattern["metadata"]["success_rate"] == 0.99
    assert retrieved_updated_pattern["metadata"]["new_field"] == "value"
    assert retrieved_updated_pattern["metadata"]["technology_stack"] == "python,django" # Old metadata fields should persist if not explicitly overwritten

    # 5. Search for the Pattern
    search_results = km.search_patterns(query="Python code patterns", limit=1)
    assert len(search_results) > 0
    assert search_results[0]["id"] == pattern_id
    assert search_results[0]["document"] == updated_doc
    assert search_results[0]["metadata"]["technology_stack"] == "python,django"
    assert search_results[0]["similarity_score"] > 0.0 # Should be > 0 with mock embedding

    # 6. Add a Category and Assign Pattern
    category_id = km.create_category(name="Python Patterns", description="Patterns related to Python.")
    assert category_id is not None
    assigned = km.assign_pattern_to_category(pattern_id, category_id)
    assert assigned

    patterns_in_cat = km.get_patterns_by_category(category_id)
    assert pattern_id in patterns_in_cat

    categories_for_pattern = km.get_pattern_categories(pattern_id)
    assert any(c["id"] == category_id for c in categories_for_pattern)

    # 7. Delete the Pattern
    deleted = km.delete_pattern(pattern_id)
    assert deleted
    assert km.get_pattern(pattern_id) is None

    # Verify pattern is also removed from category links
    patterns_in_cat_after_delete = km.get_patterns_by_category(category_id)
    assert pattern_id not in patterns_in_cat_after_delete

    # 8. Delete the Project
    deleted_project = km.delete_project(project_id)
    assert deleted_project
    assert km.get_project(project_id) is None


@pytest.mark.integration
def test_knowledge_manager_full_lifecycle_error_solution(knowledge_manager_instance):
    km = knowledge_manager_instance

    # 1. Add an Error Solution
    solution_data = {
        "document": "Error: Connection refused. Solution: Check network configuration.",
        "metadata": {
            "error_category": "Network",
            "resolution_steps": "1. Verify IP; 2. Check firewall; 3. Restart service",
            "avg_resolution_time": 30.5
        }
    }
    solution_id = km.add_error_solution(solution_data)
    assert solution_id is not None

    # 2. Retrieve the Error Solution
    retrieved_solution = km.get_error_solution(solution_id)
    assert retrieved_solution is not None
    assert retrieved_solution["id"] == solution_id
    assert retrieved_solution["document"] == "Error: Connection refused. Solution: Check network configuration."
    assert retrieved_solution["metadata"]["error_category"] == "Network"
    assert "embedding" in retrieved_solution and retrieved_solution["embedding"] is not None

    # 3. Search for the Error Solution
    search_results = km.search_error_solutions(error_query="Connection issues", limit=1)
    assert len(search_results) > 0
    assert search_results[0]["id"] == solution_id
    assert search_results[0]["document"] == "Error: Connection refused. Solution: Check network configuration."
    assert search_results[0]["similarity_score"] > 0.0

    # 4. Delete the Error Solution
    deleted = km.delete_error_solution(solution_id)
    assert deleted
    assert km.get_error_solution(solution_id) is None

@pytest.mark.integration
def test_compatibility_matrix_crud(knowledge_manager_instance):
    km = knowledge_manager_instance

    entry_id = km.add_compatibility_entry("React", "Node.js", 0.95, "Excellent compatibility")
    assert entry_id is not None

    retrieved = km.get_compatibility_entry(entry_id)
    assert retrieved["source_tech"] == "React"
    assert retrieved["compatibility_score"] == 0.95

    updated = km.update_compatibility_entry(entry_id, {"compatibility_score": 0.98, "notes": "Perfect match"})
    assert updated
    assert km.get_compatibility_entry(entry_id)["compatibility_score"] == 0.98

    search_results = km.search_compatibility_entries(source_tech="React", min_score=0.9)
    assert len(search_results) == 1
    assert search_results[0]["id"] == entry_id

    deleted = km.delete_compatibility_entry(entry_id)
    assert deleted
    assert km.get_compatibility_entry(entry_id) is None

