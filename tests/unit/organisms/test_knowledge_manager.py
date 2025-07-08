from unittest.mock import MagicMock, patch

import pytest

from src.uckn.core.organisms.knowledge_manager import KnowledgeManager
from src.uckn.storage import UnifiedDatabase  # Import UnifiedDatabase for patching


@pytest.fixture
def mock_unified_db():
    db = MagicMock(spec=UnifiedDatabase)  # Specify spec for better mock behavior
    db.is_available.return_value = True
    # Mock methods called by KnowledgeManager's public API
    db.add_project.return_value = "proj-1"
    db.get_project.return_value = {"id": "proj-1", "name": "Test Project"}
    db.update_project.return_value = True
    db.delete_project.return_value = True
    db.get_all_projects.return_value = [{"id": "proj-1", "name": "Test Project"}]
    db.add_pattern.return_value = "pattern-1"
    db.get_pattern.return_value = {"id": "pattern-1", "document": "test pattern"}
    db.update_pattern.return_value = True
    db.delete_pattern.return_value = True
    db.search_patterns.return_value = [{"id": "pattern-1", "document": "found pattern"}]
    db.add_category.return_value = "cat-1"
    db.get_category.return_value = {"id": "cat-1", "name": "Test Category"}
    db.update_category.return_value = True
    db.delete_category.return_value = True
    db.assign_pattern_to_category.return_value = True
    db.remove_pattern_from_category.return_value = True
    db.get_patterns_by_category.return_value = ["pattern-1"]
    db.get_pattern_categories.return_value = [{"id": "cat-1", "name": "Test Category"}]
    db.add_error_solution.return_value = "sol-1"
    db.get_error_solution.return_value = {"id": "sol-1", "document": "test solution"}
    db.search_error_solutions.return_value = [
        {"id": "sol-1", "document": "found solution"}
    ]
    db.add_team_access.return_value = "access-1"
    db.get_team_access.return_value = {
        "id": "access-1",
        "user_id": "user1",
        "project_id": "proj-1",
        "role": "admin",
    }
    db.update_team_access.return_value = True
    db.delete_team_access.return_value = True
    db.get_team_access_for_project.return_value = [
        {"id": "access-1", "user_id": "user1"}
    ]
    db.add_compatibility_entry.return_value = "comp-1"
    db.get_compatibility_entry.return_value = {
        "id": "comp-1",
        "source_tech": "Python",
        "target_tech": "Django",
    }
    db.update_compatibility_entry.return_value = True
    db.delete_compatibility_entry.return_value = True
    db.search_compatibility_entries.return_value = [
        {"id": "comp-1", "source_tech": "Python"}
    ]
    db.search_patterns_by_metadata.return_value = [
        {"id": "pattern-approved", "status": "approved"}
    ]
    return db


@pytest.fixture
def mock_semantic_search():
    search = MagicMock()
    search.is_available.return_value = True
    search.encode.return_value = [0.1, 0.2, 0.3]  # Mock an embedding
    return search


@pytest.fixture
def mock_tech_detector():
    return MagicMock()


@pytest.fixture
def manager(monkeypatch, mock_unified_db, mock_semantic_search, mock_tech_detector):
    # Patch the classes that KnowledgeManager instantiates
    monkeypatch.setattr(
        "src.uckn.core.organisms.knowledge_manager.UnifiedDatabase",
        lambda *a, **kw: mock_unified_db,
    )
    monkeypatch.setattr(
        "src.uckn.core.organisms.knowledge_manager.SemanticSearch",
        lambda *a, **kw: mock_semantic_search,
    )
    monkeypatch.setattr(
        "src.uckn.core.organisms.knowledge_manager.TechStackDetector",
        lambda *a, **kw: mock_tech_detector,
    )
    # No need to patch PatternManager, ErrorSolutionManager, PatternClassification as KM's public methods
    # delegate to unified_db and semantic_search directly, not these internal managers.
    return KnowledgeManager(knowledge_dir="/tmp/uckn-test-knowledge")


def test_initialization_default(monkeypatch):
    # Patch dependencies to avoid real file system or DB
    with patch(
        "src.uckn.core.organisms.knowledge_manager.UnifiedDatabase"
    ) as unified_db_patch, patch(
        "src.uckn.core.organisms.knowledge_manager.SemanticSearch"
    ) as search_patch, patch(
        "src.uckn.core.organisms.knowledge_manager.PatternManager"
    ), patch("src.uckn.core.organisms.knowledge_manager.ErrorSolutionManager"), patch(
        "src.uckn.core.organisms.knowledge_manager.PatternClassification"
    ), patch("src.uckn.core.organisms.knowledge_manager.TechStackDetector"):
        unified_db_patch.return_value.is_available.return_value = True
        search_patch.return_value.is_available.return_value = True
        km = KnowledgeManager()
        assert km.knowledge_dir.exists()
        assert km.unified_db.is_available()  # Changed from chroma_connector
        assert km.semantic_search.is_available()


def test_initialization_unavailable(monkeypatch):
    with patch(
        "src.uckn.core.organisms.knowledge_manager.UnifiedDatabase"
    ) as unified_db_patch, patch(
        "src.uckn.core.organisms.knowledge_manager.SemanticSearch"
    ) as search_patch, patch(
        "src.uckn.core.organisms.knowledge_manager.PatternManager"
    ), patch("src.uckn.core.organisms.knowledge_manager.ErrorSolutionManager"), patch(
        "src.uckn.core.organisms.knowledge_manager.PatternClassification"
    ), patch("src.uckn.core.organisms.knowledge_manager.TechStackDetector"):
        unified_db_patch.return_value.is_available.return_value = False
        search_patch.return_value.is_available.return_value = False
        km = KnowledgeManager()
        assert not km.unified_db.is_available()  # Changed from chroma_connector
        assert not km.semantic_search.is_available()


# Project management tests
def test_add_project(manager, mock_unified_db):
    project_data = {"name": "New Project", "description": "A test project"}
    result = manager.add_project(project_data["name"], project_data["description"])
    assert result == "proj-1"
    mock_unified_db.add_project.assert_called_once_with(
        project_data["name"], project_data["description"]
    )


def test_get_project(manager, mock_unified_db):
    result = manager.get_project("proj-1")
    assert result == {"id": "proj-1", "name": "Test Project"}
    mock_unified_db.get_project.assert_called_once_with("proj-1")


def test_update_project(manager, mock_unified_db):
    updates = {"name": "Updated Project"}
    result = manager.update_project("proj-1", updates)
    assert result is True
    mock_unified_db.update_project.assert_called_once_with("proj-1", updates)


def test_delete_project(manager, mock_unified_db):
    result = manager.delete_project("proj-1")
    assert result is True
    mock_unified_db.delete_project.assert_called_once_with("proj-1")


def test_get_all_projects(manager, mock_unified_db):
    result = manager.get_all_projects()
    assert result == [{"id": "proj-1", "name": "Test Project"}]
    mock_unified_db.get_all_projects.assert_called_once()


# Pattern management tests
def test_add_pattern(manager, mock_unified_db, mock_semantic_search):
    pattern_data = {
        "document": "This is a test pattern.",
        "metadata": {"foo": "bar"},
        "project_id": "proj-1",
    }
    mock_semantic_search.encode.return_value = [
        0.1,
        0.2,
        0.3,
    ]  # Ensure embedding is returned
    result = manager.add_pattern(pattern_data)
    assert result == "pattern-1"
    mock_semantic_search.encode.assert_called_once_with(pattern_data["document"])
    mock_unified_db.add_pattern.assert_called_once_with(
        document_text=pattern_data["document"],
        embedding=[0.1, 0.2, 0.3],
        metadata=pattern_data["metadata"],
        pattern_id=None,
        project_id=pattern_data["project_id"],
    )


def test_get_pattern(manager, mock_unified_db):
    result = manager.get_pattern("pattern-1")
    assert result == {"id": "pattern-1", "document": "test pattern"}
    mock_unified_db.get_pattern.assert_called_once_with("pattern-1")


def test_update_pattern(manager, mock_unified_db, mock_semantic_search):
    updates = {
        "document": "updated document",
        "metadata": {"foo": "baz"},
        "project_id": "proj-1",
    }
    mock_semantic_search.encode.return_value = [0.4, 0.5, 0.6]  # Mock new embedding
    result = manager.update_pattern("pattern-1", updates)
    assert result is True
    mock_semantic_search.encode.assert_called_once_with(updates["document"])
    mock_unified_db.update_pattern.assert_called_once_with(
        pattern_id="pattern-1",
        document_text=updates["document"],
        embedding=[0.4, 0.5, 0.6],
        metadata=updates["metadata"],
        project_id=updates["project_id"],
    )


def test_delete_pattern(manager, mock_unified_db):
    result = manager.delete_pattern("pattern-1")
    assert result is True
    mock_unified_db.delete_pattern.assert_called_once_with("pattern-1")


def test_search_patterns(manager, mock_unified_db, mock_semantic_search):
    query = "query"
    limit = 5
    min_similarity = 0.8
    metadata_filter = {"foo": "bar"}
    mock_semantic_search.encode.return_value = [0.7, 0.8, 0.9]  # Mock query embedding
    result = manager.search_patterns(
        query,
        limit=limit,
        min_similarity=min_similarity,
        metadata_filter=metadata_filter,
    )
    assert result == [{"id": "pattern-1", "document": "found pattern"}]
    mock_semantic_search.encode.assert_called_once_with(query)
    mock_unified_db.search_patterns.assert_called_once_with(
        [0.7, 0.8, 0.9], limit, min_similarity, metadata_filter
    )


# Pattern classification tests
def test_create_category(manager, mock_unified_db):
    result = manager.create_category("cat", "desc")
    assert result == "cat-1"
    mock_unified_db.add_category.assert_called_once_with("cat", "desc", None)


def test_get_category(manager, mock_unified_db):
    result = manager.get_category("cat-1")
    assert result == {"id": "cat-1", "name": "Test Category"}
    mock_unified_db.get_category.assert_called_once_with("cat-1")


def test_update_category(manager, mock_unified_db):
    result = manager.update_category("cat-1", name="new", description="desc")
    assert result is True
    mock_unified_db.update_category.assert_called_once_with(
        "cat-1", {"name": "new", "description": "desc"}
    )


def test_delete_category(manager, mock_unified_db):
    result = manager.delete_category("cat-1")
    assert result is True
    mock_unified_db.delete_category.assert_called_once_with("cat-1")


def test_assign_pattern_to_category(manager, mock_unified_db):
    result = manager.assign_pattern_to_category("pattern-1", "cat-1")
    assert result is True
    mock_unified_db.assign_pattern_to_category.assert_called_once_with(
        "pattern-1", "cat-1"
    )


def test_remove_pattern_from_category(manager, mock_unified_db):
    result = manager.remove_pattern_from_category("pattern-1", "cat-1")
    assert result is True
    mock_unified_db.remove_pattern_from_category.assert_called_once_with(
        "pattern-1", "cat-1"
    )


def test_get_patterns_by_category(manager, mock_unified_db):
    result = manager.get_patterns_by_category("cat-1")
    assert result == ["pattern-1"]
    mock_unified_db.get_patterns_by_category.assert_called_once_with("cat-1")


def test_get_pattern_categories(manager, mock_unified_db):
    result = manager.get_pattern_categories("pattern-1")
    assert result == [{"id": "cat-1", "name": "Test Category"}]
    mock_unified_db.get_pattern_categories.assert_called_once_with("pattern-1")


# Error solution management tests
def test_add_error_solution(manager, mock_unified_db, mock_semantic_search):
    solution_data = {
        "document": "This is a test solution.",
        "metadata": {"foo": "bar"},
        "project_id": "proj-1",
    }
    mock_semantic_search.encode.return_value = [
        0.1,
        0.2,
        0.3,
    ]  # Ensure embedding is returned
    result = manager.add_error_solution(solution_data)
    assert result == "sol-1"
    mock_semantic_search.encode.assert_called_once_with(solution_data["document"])
    mock_unified_db.add_error_solution.assert_called_once_with(
        document_text=solution_data["document"],
        embedding=[0.1, 0.2, 0.3],
        metadata=solution_data["metadata"],
        solution_id=None,
        project_id=solution_data["project_id"],
    )


def test_get_error_solution(manager, mock_unified_db):
    result = manager.get_error_solution("sol-1")
    assert result == {"id": "sol-1", "document": "test solution"}
    mock_unified_db.get_error_solution.assert_called_once_with("sol-1")


def test_search_error_solutions(manager, mock_unified_db, mock_semantic_search):
    error_query = "err"
    limit = 5
    min_similarity = 0.8
    metadata_filter = {"foo": "bar"}
    mock_semantic_search.encode.return_value = [0.7, 0.8, 0.9]  # Mock query embedding
    result = manager.search_error_solutions(
        error_query,
        limit=limit,
        min_similarity=min_similarity,
        metadata_filter=metadata_filter,
    )
    assert result == [{"id": "sol-1", "document": "found solution"}]
    mock_semantic_search.encode.assert_called_once_with(error_query)
    mock_unified_db.search_error_solutions.assert_called_once_with(
        [0.7, 0.8, 0.9], limit, min_similarity, metadata_filter
    )


# Team Access Management tests
def test_add_team_access(manager, mock_unified_db):
    result = manager.add_team_access("user1", "proj-1", "admin")
    assert result == "access-1"
    mock_unified_db.add_team_access.assert_called_once_with("user1", "proj-1", "admin")


def test_get_team_access(manager, mock_unified_db):
    result = manager.get_team_access("access-1")
    assert result == {
        "id": "access-1",
        "user_id": "user1",
        "project_id": "proj-1",
        "role": "admin",
    }
    mock_unified_db.get_team_access.assert_called_once_with("access-1")


def test_update_team_access(manager, mock_unified_db):
    updates = {"role": "viewer"}
    result = manager.update_team_access("access-1", updates)
    assert result is True
    mock_unified_db.update_team_access.assert_called_once_with("access-1", updates)


def test_delete_team_access(manager, mock_unified_db):
    result = manager.delete_team_access("access-1")
    assert result is True
    mock_unified_db.delete_team_access.assert_called_once_with("access-1")


def test_get_team_access_for_project(manager, mock_unified_db):
    result = manager.get_team_access_for_project("proj-1")
    assert result == [{"id": "access-1", "user_id": "user1"}]
    mock_unified_db.get_team_access_for_project.assert_called_once_with("proj-1")


# Compatibility Matrix Management tests
def test_add_compatibility_entry(manager, mock_unified_db):
    result = manager.add_compatibility_entry(
        "Python", "Django", 0.9, "Good compatibility"
    )
    assert result == "comp-1"
    mock_unified_db.add_compatibility_entry.assert_called_once_with(
        "Python", "Django", 0.9, "Good compatibility"
    )


def test_get_compatibility_entry(manager, mock_unified_db):
    result = manager.get_compatibility_entry("comp-1")
    assert result == {"id": "comp-1", "source_tech": "Python", "target_tech": "Django"}
    mock_unified_db.get_compatibility_entry.assert_called_once_with("comp-1")


def test_update_compatibility_entry(manager, mock_unified_db):
    updates = {"compatibility_score": 0.95}
    result = manager.update_compatibility_entry("comp-1", updates)
    assert result is True
    mock_unified_db.update_compatibility_entry.assert_called_once_with(
        "comp-1", updates
    )


def test_delete_compatibility_entry(manager, mock_unified_db):
    result = manager.delete_compatibility_entry("comp-1")
    assert result is True
    mock_unified_db.delete_compatibility_entry.assert_called_once_with("comp-1")


def test_search_compatibility_entries(manager, mock_unified_db):
    result = manager.search_compatibility_entries(source_tech="Python")
    assert result == [{"id": "comp-1", "source_tech": "Python"}]
    mock_unified_db.search_compatibility_entries.assert_called_once_with(
        "Python", None, None, None
    )


# Tech stack analysis
def test_analyze_project_stack(manager, mock_tech_detector):
    mock_tech_detector.analyze_project.return_value = {"stack": ["python"]}
    result = manager.analyze_project_stack("/tmp/project")
    assert result == {"stack": ["python"]}
    mock_tech_detector.analyze_project.assert_called_once_with("/tmp/project")


def test_get_all_patterns_by_status(manager, mock_unified_db):
    status = "approved"
    result = manager.get_all_patterns_by_status(status)
    assert result == [{"id": "pattern-approved", "status": "approved"}]
    mock_unified_db.search_patterns_by_metadata.assert_called_once_with(
        {"status": status}
    )


def test_get_health_status(manager, mock_unified_db, mock_semantic_search):
    mock_unified_db.is_available.return_value = True
    mock_semantic_search.is_available.return_value = True
    result = manager.get_health_status()
    assert result["unified_db_available"] is True  # Changed from chromadb_available
    assert result["semantic_search_available"] is True
    assert "pattern_manager" in result["components"]


def test_health_status_unavailable(monkeypatch):
    with patch(
        "src.uckn.core.organisms.knowledge_manager.UnifiedDatabase"
    ) as unified_db_patch, patch(
        "src.uckn.core.organisms.knowledge_manager.SemanticSearch"
    ) as search_patch, patch(
        "src.uckn.core.organisms.knowledge_manager.PatternManager"
    ), patch("src.uckn.core.organisms.knowledge_manager.ErrorSolutionManager"), patch(
        "src.uckn.core.organisms.knowledge_manager.PatternClassification"
    ), patch("src.uckn.core.organisms.knowledge_manager.TechStackDetector"):
        unified_db_patch.return_value.is_available.return_value = False
        search_patch.return_value.is_available.return_value = False
        km = KnowledgeManager()
        status = km.get_health_status()
        assert (
            status["unified_db_available"] is False
        )  # Changed from chromadb_available
        assert status["semantic_search_available"] is False


def test_error_handling_unified_db(monkeypatch):
    # This class mimics UnifiedDatabase but raises exceptions for all its methods
    class FailingUnifiedDatabase:
        def __init__(self, pg_db_url, chroma_db_path):
            pass  # Accept constructor arguments

        def is_available(self):
            return True  # Must be available for other methods to be called

        def add_project(self, *a, **kw):
            raise Exception("fail add_project")

        def get_project(self, *a, **kw):
            raise Exception("fail get_project")

        def update_project(self, *a, **kw):
            raise Exception("fail update_project")

        def delete_project(self, *a, **kw):
            raise Exception("fail delete_project")

        def get_all_projects(self, *a, **kw):
            raise Exception("fail get_all_projects")

        def add_pattern(self, *a, **kw):
            raise Exception("fail add_pattern")

        def get_pattern(self, *a, **kw):
            raise Exception("fail get_pattern")

        def update_pattern(self, *a, **kw):
            raise Exception("fail update_pattern")

        def delete_pattern(self, *a, **kw):
            raise Exception("fail delete_pattern")

        def search_patterns(self, *a, **kw):
            raise Exception("fail search_patterns")

        def add_category(self, *a, **kw):
            raise Exception("fail add_category")

        def get_category(self, *a, **kw):
            raise Exception("fail get_category")

        def update_category(self, *a, **kw):
            raise Exception("fail update_category")

        def delete_category(self, *a, **kw):
            raise Exception("fail delete_category")

        def assign_pattern_to_category(self, *a, **kw):
            raise Exception("fail assign_pattern_to_category")

        def remove_pattern_from_category(self, *a, **kw):
            raise Exception("fail remove_pattern_from_category")

        def get_patterns_by_category(self, *a, **kw):
            raise Exception("fail get_patterns_by_category")

        def get_pattern_categories(self, *a, **kw):
            raise Exception("fail get_pattern_categories")

        def add_error_solution(self, *a, **kw):
            raise Exception("fail add_error_solution")

        def get_error_solution(self, *a, **kw):
            raise Exception("fail get_error_solution")

        def search_error_solutions(self, *a, **kw):
            raise Exception("fail search_error_solutions")

        def add_team_access(self, *a, **kw):
            raise Exception("fail add_team_access")

        def get_team_access(self, *a, **kw):
            raise Exception("fail get_team_access")

        def update_team_access(self, *a, **kw):
            raise Exception("fail update_team_access")

        def delete_team_access(self, *a, **kw):
            raise Exception("fail delete_team_access")

        def get_team_access_for_project(self, *a, **kw):
            raise Exception("fail get_team_access_for_project")

        def add_compatibility_entry(self, *a, **kw):
            raise Exception("fail add_compatibility_entry")

        def get_compatibility_entry(self, *a, **kw):
            raise Exception("fail get_compatibility_entry")

        def update_compatibility_entry(self, *a, **kw):
            raise Exception("fail update_compatibility_entry")

        def delete_compatibility_entry(self, *a, **kw):
            raise Exception("fail delete_compatibility_entry")

        def search_compatibility_entries(self, *a, **kw):
            raise Exception("fail search_compatibility_entries")

        def search_patterns_by_metadata(self, *a, **kw):
            raise Exception("fail search_patterns_by_metadata")

    with patch(
        "src.uckn.core.organisms.knowledge_manager.UnifiedDatabase",
        FailingUnifiedDatabase,
    ), patch(
        "src.uckn.core.organisms.knowledge_manager.SemanticSearch"
    ) as search_patch, patch(
        "src.uckn.core.organisms.knowledge_manager.PatternManager"
    ), patch("src.uckn.core.organisms.knowledge_manager.ErrorSolutionManager"), patch(
        "src.uckn.core.organisms.knowledge_manager.PatternClassification"
    ), patch("src.uckn.core.organisms.knowledge_manager.TechStackDetector"):
        search_patch.return_value.is_available.return_value = True
        search_patch.return_value.encode.return_value = [
            0.1,
            0.2,
            0.3,
        ]  # Mock encode for calls that need it
        km = KnowledgeManager()

        with pytest.raises(Exception, match="fail add_project"):
            km.add_project("proj")
        with pytest.raises(Exception, match="fail get_project"):
            km.get_project("proj-id")
        with pytest.raises(Exception, match="fail update_project"):
            km.update_project("proj-id", {})
        with pytest.raises(Exception, match="fail delete_project"):
            km.delete_project("proj-id")
        with pytest.raises(Exception, match="fail get_all_projects"):
            km.get_all_projects()

        with pytest.raises(Exception, match="fail add_pattern"):
            km.add_pattern({"document": "test"})
        with pytest.raises(Exception, match="fail get_pattern"):
            km.get_pattern("id")
        with pytest.raises(Exception, match="fail update_pattern"):
            km.update_pattern("id", {"document": "test"})
        with pytest.raises(Exception, match="fail delete_pattern"):
            km.delete_pattern("id")
        with pytest.raises(Exception, match="fail search_patterns"):
            km.search_patterns("q")

        with pytest.raises(Exception, match="fail add_category"):
            km.create_category("cat")
        with pytest.raises(Exception, match="fail get_category"):
            km.get_category("cat-id")
        with pytest.raises(Exception, match="fail update_category"):
            km.update_category("cat-id", name="new")
        with pytest.raises(Exception, match="fail delete_category"):
            km.delete_category("cat-id")
        with pytest.raises(Exception, match="fail assign_pattern_to_category"):
            km.assign_pattern_to_category("p", "c")
        with pytest.raises(Exception, match="fail remove_pattern_from_category"):
            km.remove_pattern_from_category("p", "c")
        with pytest.raises(Exception, match="fail get_patterns_by_category"):
            km.get_patterns_by_category("c")
        with pytest.raises(Exception, match="fail get_pattern_categories"):
            km.get_pattern_categories("p")

        with pytest.raises(Exception, match="fail add_error_solution"):
            km.add_error_solution({"document": "test"})
        with pytest.raises(Exception, match="fail get_error_solution"):
            km.get_error_solution("id")
        with pytest.raises(Exception, match="fail search_error_solutions"):
            km.search_error_solutions("q")

        with pytest.raises(Exception, match="fail add_team_access"):
            km.add_team_access("u", "p", "r")
        with pytest.raises(Exception, match="fail get_team_access"):
            km.get_team_access("id")
        with pytest.raises(Exception, match="fail update_team_access"):
            km.update_team_access("id", {})
        with pytest.raises(Exception, match="fail delete_team_access"):
            km.delete_team_access("id")
        with pytest.raises(Exception, match="fail get_team_access_for_project"):
            km.get_team_access_for_project("p")

        with pytest.raises(Exception, match="fail add_compatibility_entry"):
            km.add_compatibility_entry("a", "b", 1.0)
        with pytest.raises(Exception, match="fail get_compatibility_entry"):
            km.get_compatibility_entry("id")
        with pytest.raises(Exception, match="fail update_compatibility_entry"):
            km.update_compatibility_entry("id", {})
        with pytest.raises(Exception, match="fail delete_compatibility_entry"):
            km.delete_compatibility_entry("id")
        with pytest.raises(Exception, match="fail search_compatibility_entries"):
            km.search_compatibility_entries()

        with pytest.raises(Exception, match="fail search_patterns_by_metadata"):
            km.get_all_patterns_by_status("status")
