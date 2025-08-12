from unittest.mock import MagicMock, patch

import pytest

from src.uckn.core.organisms.knowledge_manager import KnowledgeManager


@pytest.fixture
def mock_chroma():
    chroma = MagicMock()
    chroma.is_available.return_value = True
    return chroma


@pytest.fixture
def mock_semantic_search():
    search = MagicMock()
    search.is_available.return_value = True
    return search


@pytest.fixture
def mock_pattern_manager():
    return MagicMock()


@pytest.fixture
def mock_error_solution_manager():
    return MagicMock()


@pytest.fixture
def mock_pattern_classification():
    return MagicMock()


@pytest.fixture
def mock_tech_detector():
    return MagicMock()


@pytest.fixture
def mock_unified_db():
    unified_db = MagicMock()
    unified_db.is_available.return_value = True
    return unified_db


@pytest.fixture
def manager(
    monkeypatch,
    mock_unified_db,
    mock_semantic_search,
    mock_pattern_manager,
    mock_error_solution_manager,
    mock_pattern_classification,
    mock_tech_detector,
):
    # Patch all dependencies
    monkeypatch.setattr(
        "src.uckn.core.organisms.knowledge_manager.UnifiedDatabase",
        lambda *a, **kw: mock_unified_db,
    )
    monkeypatch.setattr(
        "src.uckn.core.organisms.knowledge_manager.SemanticSearch",
        lambda *a, **kw: mock_semantic_search,
    )
    monkeypatch.setattr(
        "src.uckn.core.organisms.knowledge_manager.PatternManager",
        lambda *a, **kw: mock_pattern_manager,
    )
    monkeypatch.setattr(
        "src.uckn.core.organisms.knowledge_manager.ErrorSolutionManager",
        lambda *a, **kw: mock_error_solution_manager,
    )
    monkeypatch.setattr(
        "src.uckn.core.organisms.knowledge_manager.PatternClassification",
        lambda *a, **kw: mock_pattern_classification,
    )
    monkeypatch.setattr(
        "src.uckn.core.organisms.knowledge_manager.TechStackDetector",
        lambda *a, **kw: mock_tech_detector,
    )
    return KnowledgeManager(knowledge_dir="/tmp/uckn-test-knowledge")


def test_initialization_default(monkeypatch):
    # Patch dependencies to avoid real file system or DB
    with (
        patch(
            "src.uckn.core.organisms.knowledge_manager.UnifiedDatabase"
        ) as unified_db_patch,
        patch(
            "src.uckn.core.organisms.knowledge_manager.SemanticSearch"
        ) as search_patch,
        patch("src.uckn.core.organisms.knowledge_manager.PatternManager"),
        patch("src.uckn.core.organisms.knowledge_manager.ErrorSolutionManager"),
        patch("src.uckn.core.organisms.knowledge_manager.PatternClassification"),
        patch("src.uckn.core.organisms.knowledge_manager.TechStackDetector"),
    ):
        unified_db_patch.return_value.is_available.return_value = True
        search_patch.return_value.is_available.return_value = True
        km = KnowledgeManager()
        assert km.knowledge_dir.exists()
        assert km.unified_db.is_available()
        assert km.semantic_search.is_available()


def test_initialization_unavailable(monkeypatch):
    with (
        patch(
            "src.uckn.core.organisms.knowledge_manager.UnifiedDatabase"
        ) as unified_db_patch,
        patch(
            "src.uckn.core.organisms.knowledge_manager.SemanticSearch"
        ) as search_patch,
        patch("src.uckn.core.organisms.knowledge_manager.PatternManager"),
        patch("src.uckn.core.organisms.knowledge_manager.ErrorSolutionManager"),
        patch("src.uckn.core.organisms.knowledge_manager.PatternClassification"),
        patch("src.uckn.core.organisms.knowledge_manager.TechStackDetector"),
    ):
        unified_db_patch.return_value.is_available.return_value = False
        search_patch.return_value.is_available.return_value = False
        km = KnowledgeManager()
        assert not km.unified_db.is_available()
        assert not km.semantic_search.is_available()


def test_add_pattern(manager, mock_pattern_manager):
    mock_pattern_manager.add_pattern.return_value = "pattern-1"
    result = manager.add_pattern({"foo": "bar"})
    assert result == "pattern-1"
    mock_pattern_manager.add_pattern.assert_called_once()


def test_get_pattern(manager, mock_pattern_manager):
    mock_pattern_manager.get_pattern.return_value = {"id": "pattern-1"}
    result = manager.get_pattern("pattern-1")
    assert result == {"id": "pattern-1"}
    mock_pattern_manager.get_pattern.assert_called_once_with("pattern-1")


def test_update_pattern(manager, mock_pattern_manager):
    mock_pattern_manager.update_pattern.return_value = True
    result = manager.update_pattern("pattern-1", {"foo": "bar"})
    assert result is True
    mock_pattern_manager.update_pattern.assert_called_once()


def test_delete_pattern(manager, mock_pattern_manager):
    mock_pattern_manager.delete_pattern.return_value = True
    result = manager.delete_pattern("pattern-1")
    assert result is True
    mock_pattern_manager.delete_pattern.assert_called_once()


def test_search_patterns(manager, mock_pattern_manager):
    mock_pattern_manager.search_patterns.return_value = [{"id": "pattern-1"}]
    result = manager.search_patterns(
        "query", limit=5, min_similarity=0.8, metadata_filter={"foo": "bar"}
    )
    assert result == [{"id": "pattern-1"}]
    mock_pattern_manager.search_patterns.assert_called_once()


def test_create_category(manager, mock_pattern_classification):
    mock_pattern_classification.add_category.return_value = "cat-1"
    result = manager.create_category("cat", "desc")
    assert result == "cat-1"
    mock_pattern_classification.add_category.assert_called_once()


def test_get_category(manager, mock_pattern_classification):
    mock_pattern_classification.get_category.return_value = {"id": "cat-1"}
    result = manager.get_category("cat-1")
    assert result == {"id": "cat-1"}
    mock_pattern_classification.get_category.assert_called_once_with("cat-1")


def test_update_category(manager, mock_pattern_classification):
    mock_pattern_classification.update_category.return_value = True
    result = manager.update_category("cat-1", name="new", description="desc")
    assert result is True
    mock_pattern_classification.update_category.assert_called_once()


def test_delete_category(manager, mock_pattern_classification):
    mock_pattern_classification.delete_category.return_value = True
    result = manager.delete_category("cat-1")
    assert result is True
    mock_pattern_classification.delete_category.assert_called_once()


def test_assign_pattern_to_category(manager, mock_pattern_classification):
    mock_pattern_classification.assign_pattern_to_category.return_value = True
    result = manager.assign_pattern_to_category("pattern-1", "cat-1")
    assert result is True
    mock_pattern_classification.assign_pattern_to_category.assert_called_once()


def test_remove_pattern_from_category(manager, mock_pattern_classification):
    mock_pattern_classification.remove_pattern_from_category.return_value = True
    result = manager.remove_pattern_from_category("pattern-1", "cat-1")
    assert result is True
    mock_pattern_classification.remove_pattern_from_category.assert_called_once()


def test_get_patterns_by_category(manager, mock_pattern_classification):
    mock_pattern_classification.get_patterns_in_category.return_value = ["pattern-1"]
    result = manager.get_patterns_by_category("cat-1")
    assert result == ["pattern-1"]
    mock_pattern_classification.get_patterns_in_category.assert_called_once_with(
        "cat-1"
    )


def test_get_pattern_categories(manager, mock_pattern_classification):
    mock_pattern_classification.get_categories_for_pattern.return_value = [
        {"id": "cat-1"}
    ]
    result = manager.get_pattern_categories("pattern-1")
    assert result == [{"id": "cat-1"}]
    mock_pattern_classification.get_categories_for_pattern.assert_called_once_with(
        "pattern-1"
    )


def test_add_error_solution(manager, mock_error_solution_manager):
    mock_error_solution_manager.add_error_solution.return_value = "sol-1"
    result = manager.add_error_solution({"foo": "bar"})
    assert result == "sol-1"
    mock_error_solution_manager.add_error_solution.assert_called_once()


def test_get_error_solution(manager, mock_error_solution_manager):
    mock_error_solution_manager.get_error_solution.return_value = {"id": "sol-1"}
    result = manager.get_error_solution("sol-1")
    assert result == {"id": "sol-1"}
    mock_error_solution_manager.get_error_solution.assert_called_once_with("sol-1")


def test_search_error_solutions(manager, mock_error_solution_manager):
    mock_error_solution_manager.search_error_solutions.return_value = [{"id": "sol-1"}]
    result = manager.search_error_solutions(
        "err", limit=5, min_similarity=0.8, metadata_filter={"foo": "bar"}
    )
    assert result == [{"id": "sol-1"}]
    mock_error_solution_manager.search_error_solutions.assert_called_once()


def test_analyze_project_stack(manager, mock_tech_detector):
    mock_tech_detector.analyze_project.return_value = {"stack": ["python"]}
    result = manager.analyze_project_stack("/tmp/project")
    assert result == {"stack": ["python"]}
    mock_tech_detector.analyze_project.assert_called_once_with("/tmp/project")


def test_get_health_status(manager, mock_unified_db, mock_semantic_search):
    mock_unified_db.is_available.return_value = True
    mock_semantic_search.is_available.return_value = True
    result = manager.get_health_status()
    assert result["unified_db_available"] is True
    assert result["semantic_search_available"] is True
    assert "pattern_manager" in result["components"]


def test_health_status_unavailable(monkeypatch):
    with (
        patch(
            "src.uckn.core.organisms.knowledge_manager.UnifiedDatabase"
        ) as unified_db_patch,
        patch(
            "src.uckn.core.organisms.knowledge_manager.SemanticSearch"
        ) as search_patch,
        patch("src.uckn.core.organisms.knowledge_manager.PatternManager"),
        patch("src.uckn.core.organisms.knowledge_manager.ErrorSolutionManager"),
        patch("src.uckn.core.organisms.knowledge_manager.PatternClassification"),
        patch("src.uckn.core.organisms.knowledge_manager.TechStackDetector"),
    ):
        unified_db_patch.return_value.is_available.return_value = False
        search_patch.return_value.is_available.return_value = False
        km = KnowledgeManager()
        status = km.get_health_status()
        assert status["chromadb_available"] is False
        assert status["semantic_search_available"] is False


def test_error_handling_pattern_manager(monkeypatch):
    # Simulate pattern_manager raising
    class FailingPatternManager:
        def add_pattern(self, *a, **kw):
            raise Exception("fail")

        def get_pattern(self, *a, **kw):
            raise Exception("fail")

        def update_pattern(self, *a, **kw):
            raise Exception("fail")

        def delete_pattern(self, *a, **kw):
            raise Exception("fail")

        def search_patterns(self, *a, **kw):
            raise Exception("fail")

    with (
        patch(
            "src.uckn.core.organisms.knowledge_manager.PatternManager",
            FailingPatternManager,
        ),
        patch(
            "src.uckn.core.organisms.knowledge_manager.UnifiedDatabase"
        ) as unified_db_patch,
        patch("src.uckn.core.organisms.knowledge_manager.SemanticSearch"),
        patch("src.uckn.core.organisms.knowledge_manager.ErrorSolutionManager"),
        patch("src.uckn.core.organisms.knowledge_manager.PatternClassification"),
        patch("src.uckn.core.organisms.knowledge_manager.TechStackDetector"),
    ):
        unified_db_patch.return_value.is_available.return_value = True
        km = KnowledgeManager()
        with pytest.raises((ValueError, RuntimeError, TypeError)):
            km.add_pattern({})
        with pytest.raises((ValueError, RuntimeError, TypeError)):
            km.get_pattern("id")
        with pytest.raises((ValueError, RuntimeError, TypeError)):
            km.update_pattern("id", {})
        with pytest.raises((ValueError, RuntimeError, TypeError)):
            km.delete_pattern("id")
        with pytest.raises((ValueError, RuntimeError, TypeError)):
            km.search_patterns("q")


def test_error_handling_error_solution_manager(monkeypatch):
    class FailingErrorSolutionManager:
        def add_error_solution(self, *a, **kw):
            raise Exception("fail")

        def get_error_solution(self, *a, **kw):
            raise Exception("fail")

        def search_error_solutions(self, *a, **kw):
            raise Exception("fail")

    with (
        patch(
            "src.uckn.core.organisms.knowledge_manager.ErrorSolutionManager",
            FailingErrorSolutionManager,
        ),
        patch(
            "src.uckn.core.organisms.knowledge_manager.UnifiedDatabase"
        ) as unified_db_patch,
        patch("src.uckn.core.organisms.knowledge_manager.SemanticSearch"),
        patch("src.uckn.core.organisms.knowledge_manager.PatternManager"),
        patch("src.uckn.core.organisms.knowledge_manager.PatternClassification"),
        patch("src.uckn.core.organisms.knowledge_manager.TechStackDetector"),
    ):
        unified_db_patch.return_value.is_available.return_value = True
        km = KnowledgeManager()
        with pytest.raises((ValueError, RuntimeError, TypeError)):
            km.add_error_solution({})
        with pytest.raises((ValueError, RuntimeError, TypeError)):
            km.get_error_solution("id")
        with pytest.raises((ValueError, RuntimeError, TypeError)):
            km.search_error_solutions("q")
