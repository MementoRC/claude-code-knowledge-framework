import os
import shutil
import tempfile
import time

import psycopg
import pytest

from src.uckn.core.organisms.knowledge_manager import KnowledgeManager


def _check_database_available():
    """Check if PostgreSQL database is available for testing."""
    try:
        import psycopg
        conn = psycopg.connect("postgresql://localhost:5432/postgres", connect_timeout=2)
        conn.close()
        return True
    except (ImportError, psycopg.OperationalError, Exception):
        return False


requires_database = pytest.mark.skipif(
    not _check_database_available(),
    reason="PostgreSQL database not available - skipping integration tests"
)


@pytest.fixture(scope="module")
def temp_knowledge_dir():
    temp_dir = tempfile.mkdtemp(prefix="uckn_e2e_basic_")
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="module")
def km(temp_knowledge_dir):
    km = KnowledgeManager(knowledge_dir=temp_knowledge_dir)
    yield km


@requires_database
def test_basic_end_to_end_workflow(km):
    """Test basic end-to-end workflow: add → retrieve → update → delete"""

    # 1. Add a pattern
    pattern = {
        "document": "Use factory pattern for object creation.",
        "metadata": {
            "pattern_id": "factory1",
            "pattern_type": "creational",
            "technology_stack": "python",
            "success_rate": 0.85,
            "created_at": "2024-06-28T12:00:00Z",
            "updated_at": "2024-06-28T12:00:00Z",
        },
    }
    pattern_id = km.add_pattern(pattern)
    assert pattern_id is not None

    # 2. Retrieve the pattern
    retrieved = km.get_pattern(pattern_id)
    assert retrieved is not None
    assert retrieved["document"] == pattern["document"]
    assert retrieved["metadata"]["pattern_type"] == "creational"

    # 3. Add an error solution
    solution = {
        "document": "Fix ImportError by checking module path and installation.",
        "metadata": {
            "solution_id": "import1",
            "error_category": "ImportError",
            "resolution_steps": "Check path,reinstall module",
            "avg_resolution_time": 3.0,
            "created_at": "2024-06-28T12:00:00Z",
            "updated_at": "2024-06-28T12:00:00Z",
        },
    }
    solution_id = km.add_error_solution(solution)
    assert solution_id is not None

    # 4. Retrieve the error solution
    retrieved_solution = km.get_error_solution(solution_id)
    assert retrieved_solution is not None
    assert retrieved_solution["document"] == solution["document"]
    assert retrieved_solution["metadata"]["error_category"] == "ImportError"

    # 5. Test categorization
    category_id = km.create_category("Design Patterns", "Software design patterns")
    assert category_id is not None

    assigned = km.assign_pattern_to_category(pattern_id, category_id)
    assert assigned

    patterns_in_cat = km.get_patterns_by_category(category_id)
    assert pattern_id in patterns_in_cat

    # 6. Test health status
    health = km.get_health_status()
    assert health["chromadb_available"] is True
    assert health["semantic_search_available"] is True

    # 7. Cleanup
    deleted_pattern = km.delete_pattern(pattern_id)
    assert deleted_pattern

    deleted_solution = km.error_solution_manager.delete_error_solution(solution_id)
    assert deleted_solution

    deleted_category = km.delete_category(category_id)
    assert deleted_category


@requires_database
def test_error_handling_workflow(km):
    """Test error handling in end-to-end workflow"""

    # Test non-existent retrievals
    assert km.get_pattern("nonexistent") is None
    assert km.get_error_solution("nonexistent") is None

    # Test invalid operations
    assert not km.assign_pattern_to_category("invalid", "invalid")
    assert not km.delete_pattern("nonexistent")


@requires_database
def test_tech_stack_analysis_workflow(km):
    """Test technology stack analysis workflow"""

    # Create a temporary project directory
    temp_project = tempfile.mkdtemp(prefix="test_project_")
    try:
        # Create a simple Python file
        with open(os.path.join(temp_project, "main.py"), "w") as f:
            f.write("def hello():\n    print('Hello World')\n")

        # Analyze project
        tech_stack = km.analyze_project_stack(temp_project)
        assert isinstance(tech_stack, dict)

        # Should detect Python
        languages = tech_stack.get("languages", [])
        primary = tech_stack.get("primary_language", "")
        assert "python" in str(languages).lower() or "python" in primary.lower()

    finally:
        shutil.rmtree(temp_project)
