import os
import shutil
import tempfile
import time

import pytest

from src.uckn.core.organisms.knowledge_manager import KnowledgeManager


@pytest.fixture(scope="module")
def temp_knowledge_dir():
    temp_dir = tempfile.mkdtemp(prefix="uckn_e2e_lifecycle_")
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="module")
def km(temp_knowledge_dir):
    km = KnowledgeManager(knowledge_dir=temp_knowledge_dir)
    yield km

def test_complete_knowledge_lifecycle(km):
    """Test complete knowledge lifecycle: ingestion → processing → storage → retrieval → analytics"""

    # 1. Ingestion: Add a pattern and an error solution
    pattern = {
        "document": "Use dependency injection for testable code.",
        "metadata": {
            "pattern_id": "di1",
            "pattern_type": "architecture",
            "technology_stack": "python",  # String, not list
            "success_rate": 0.92,
            "created_at": "2024-06-28T12:00:00Z",
            "updated_at": "2024-06-28T12:00:00Z"
        }
    }
    pattern_id = km.add_pattern(pattern)
    assert pattern_id is not None

    solution = {
        "document": "To fix AttributeError, check if the object has the attribute before accessing.",
        "metadata": {
            "solution_id": "attr1",
            "error_category": "AttributeError",
            "resolution_steps": "Use hasattr() before access",  # String, not list
            "avg_resolution_time": 1.0,
            "created_at": "2024-06-28T12:00:00Z",
            "updated_at": "2024-06-28T12:00:00Z"
        }
    }
    solution_id = km.add_error_solution(solution)
    assert solution_id is not None

    # 2. Processing: Verify data is processed and stored correctly
    retrieved_pattern = km.get_pattern(pattern_id)
    assert retrieved_pattern is not None
    assert retrieved_pattern["document"] == pattern["document"]

    retrieved_solution = km.get_error_solution(solution_id)
    assert retrieved_solution is not None
    assert retrieved_solution["document"] == solution["document"]

    # 3. Storage: Verify data persistence and searchability
    # Search for patterns
    pattern_results = km.search_patterns("dependency injection", limit=5)
    assert isinstance(pattern_results, list)
    assert any(r.get("id") == pattern_id for r in pattern_results)

    # Search for error solutions
    solution_results = km.search_error_solutions("AttributeError", limit=5)
    assert isinstance(solution_results, list)
    assert any(r.get("id") == solution_id for r in solution_results)

    # 4. Retrieval: Test classification and categorization
    # Create category and assign pattern
    category_id = km.create_category("Architecture Patterns", "Software architecture patterns")
    assert category_id is not None

    assigned = km.assign_pattern_to_category(pattern_id, category_id)
    assert assigned

    # Verify pattern is in category
    patterns_in_category = km.get_patterns_by_category(category_id)
    assert pattern_id in patterns_in_category

    # 5. Analytics: Test system health and metrics
    health = km.get_health_status()
    assert health["chromadb_available"] is True
    assert health["semantic_search_available"] is True
    assert "pattern_manager" in health["components"]

    # 6. Cleanup verification
    # Update pattern
    updated = km.update_pattern(pattern_id, {"metadata": {"success_rate": 0.95}})
    assert updated

    # Remove from category
    removed = km.remove_pattern_from_category(pattern_id, category_id)
    assert removed

    # Delete pattern and solution
    pattern_deleted = km.delete_pattern(pattern_id)
    assert pattern_deleted

    solution_deleted = km.error_solution_manager.delete_error_solution(solution_id)
    assert solution_deleted

def test_end_to_end_error_handling(km):
    """Test end-to-end error handling and graceful degradation"""

    # Test non-existent pattern retrieval
    result = km.get_pattern("nonexistent_pattern")
    assert result is None

    # Test non-existent error solution retrieval
    result = km.get_error_solution("nonexistent_solution")
    assert result is None

    # Test empty search results
    results = km.search_patterns("zyx_nonexistent_query_abc", limit=5)
    assert isinstance(results, list)
    assert len(results) == 0

    # Test invalid category operations
    invalid_assignment = km.assign_pattern_to_category("invalid_pattern", "invalid_category")
    assert not invalid_assignment

def test_concurrent_operations(km):
    """Test system behavior under concurrent operations"""

    # Add multiple patterns in sequence (simulating concurrent usage)
    patterns = []
    for i in range(3):
        pattern = {
            "document": f"Pattern {i} for concurrent testing.",
            "metadata": {
                "pattern_id": f"concurrent{i}",
                "pattern_type": "test",
                "technology_stack": "python",
                "success_rate": 0.8 + (i * 0.05),
                "created_at": "2024-06-28T12:00:00Z",
                "updated_at": "2024-06-28T12:00:00Z"
            }
        }
        pattern_id = km.add_pattern(pattern)
        assert pattern_id is not None
        patterns.append(pattern_id)

    # Verify all patterns are retrievable
    for pattern_id in patterns:
        retrieved = km.get_pattern(pattern_id)
        assert retrieved is not None

    # Search should find multiple patterns
    results = km.search_patterns("concurrent", limit=10)
    assert len(results) >= 3

    # Clean up
    for pattern_id in patterns:
        deleted = km.delete_pattern(pattern_id)
        assert deleted
