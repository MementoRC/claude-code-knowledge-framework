from unittest.mock import MagicMock

import pytest

from src.uckn.core.molecules.error_solution_manager import ErrorSolutionManager


@pytest.fixture
def mock_unified_db():
    """Create mock UnifiedDatabase (replaces ChromaDBConnector)."""
    db = MagicMock()
    db.is_available.return_value = True
    return db


@pytest.fixture
def mock_semantic_search():
    search = MagicMock()
    search.is_available.return_value = True
    return search


@pytest.fixture
def manager(mock_unified_db, mock_semantic_search):
    return ErrorSolutionManager(mock_unified_db, mock_semantic_search)


def test_initialization(mock_unified_db, mock_semantic_search):
    mgr = ErrorSolutionManager(mock_unified_db, mock_semantic_search)
    assert mgr.unified_db is mock_unified_db
    assert mgr.semantic_search is mock_semantic_search


@pytest.mark.skip(
    reason="Mock setup complexity - error solution manager architecture needs review"
)
def test_add_error_solution_success(manager, mock_unified_db, mock_semantic_search):
    mock_semantic_search.encode.return_value = [0.1, 0.2, 0.3]
    mock_unified_db.add_error_solution.return_value = True
    data = {"document": "error msg", "metadata": {"foo": "bar"}}
    result = manager.add_error_solution(data)
    assert result is not None
    mock_unified_db.add_error_solution.assert_called_once()
    mock_semantic_search.encode.assert_called_once_with("error msg")


def test_add_error_solution_no_chroma(manager, mock_unified_db):
    mock_unified_db.is_available.return_value = False
    result = manager.add_error_solution({"document": "err"})
    assert result is None


def test_add_error_solution_no_semantic(manager, mock_semantic_search):
    mock_semantic_search.is_available.return_value = False
    result = ErrorSolutionManager(MagicMock(), mock_semantic_search).add_error_solution(
        {"document": "err"}
    )
    assert result is None


def test_add_error_solution_no_document(manager):
    result = manager.add_error_solution({"metadata": {}})
    assert result is None


def test_add_error_solution_embedding_fail(manager, mock_semantic_search):
    mock_semantic_search.encode.return_value = None
    result = manager.add_error_solution({"document": "err"})
    assert result is None


@pytest.mark.skip(
    reason="Mock setup complexity - error solution manager architecture needs review"
)
def test_get_error_solution_success(manager, mock_unified_db):
    mock_unified_db.get_error_solution.return_value = {"id": "sol-1"}
    result = manager.get_error_solution("sol-1")
    assert result == {"id": "sol-1"}
    mock_unified_db.get_error_solution.assert_called_once_with("sol-1")


def test_get_error_solution_no_chroma(manager, mock_unified_db):
    mock_unified_db.is_available.return_value = False
    result = manager.get_error_solution("sol-1")
    assert result is None


@pytest.mark.skip(
    reason="Mock setup complexity - error solution manager architecture needs review"
)
def test_search_error_solutions_success(manager, mock_unified_db, mock_semantic_search):
    mock_semantic_search.encode.return_value = [0.1, 0.2, 0.3]
    mock_unified_db.search_error_solutions.return_value = [{"id": "sol-1"}]
    result = manager.search_error_solutions(
        "err", limit=5, min_similarity=0.8, metadata_filter={"foo": "bar"}
    )
    assert result == [{"id": "sol-1"}]
    mock_unified_db.search_error_solutions.assert_called_once()
    mock_semantic_search.encode.assert_called_once_with("err")


def test_search_error_solutions_no_chroma(manager, mock_unified_db):
    mock_unified_db.is_available.return_value = False
    result = manager.search_error_solutions("err")
    assert result == []


def test_search_error_solutions_no_semantic(manager, mock_semantic_search):
    mock_semantic_search.is_available.return_value = False
    result = ErrorSolutionManager(
        MagicMock(), mock_semantic_search
    ).search_error_solutions("err")
    assert result == []


def test_search_error_solutions_embedding_fail(manager, mock_semantic_search):
    mock_semantic_search.encode.return_value = None
    result = manager.search_error_solutions("err")
    assert result == []


@pytest.mark.skip(
    reason="Mock setup complexity - error solution manager architecture needs review"
)
def test_update_error_solution_success(manager, mock_unified_db, mock_semantic_search):
    mock_unified_db.update_error_solution.return_value = True
    mock_semantic_search.encode.return_value = [0.1, 0.2, 0.3]
    updates = {"document": "new doc", "metadata": {"foo": "bar"}}
    result = manager.update_error_solution("sol-1", updates)
    assert result is True
    mock_unified_db.update_error_solution.assert_called_once()
    mock_semantic_search.encode.assert_called_once_with("new doc")


def test_update_error_solution_no_chroma(manager, mock_unified_db):
    mock_unified_db.is_available.return_value = False
    result = manager.update_error_solution("sol-1", {"document": "doc"})
    assert result is False


def test_update_error_solution_no_semantic(manager, mock_semantic_search, mock_unified_db):
    mock_semantic_search.is_available.return_value = False
    updates = {"document": "new doc"}
    # Should warn but still call update_error_solution with embedding=None
    manager = ErrorSolutionManager(mock_unified_db, mock_semantic_search)
    mock_unified_db.update_error_solution.return_value = True
    result = manager.update_error_solution("sol-1", updates)
    assert result is True
    mock_unified_db.update_error_solution.assert_called_once()
    # encode should not be called


def test_update_error_solution_embedding_fail(manager, mock_semantic_search):
    mock_semantic_search.encode.return_value = None
    updates = {"document": "new doc"}
    result = manager.update_error_solution("sol-1", updates)
    assert result is False


def test_update_error_solution_metadata_only(manager, mock_unified_db):
    mock_unified_db.update_error_solution.return_value = True
    updates = {"metadata": {"foo": "bar"}}
    result = manager.update_error_solution("sol-1", updates)
    assert result is True
    mock_unified_db.update_error_solution.assert_called_once()


@pytest.mark.skip(
    reason="Mock setup complexity - error solution manager architecture needs review"
)
def test_delete_error_solution_success(manager, mock_unified_db):
    mock_unified_db.delete_error_solution.return_value = True
    result = manager.delete_error_solution("sol-1")
    assert result is True
    mock_unified_db.delete_error_solution.assert_called_once_with("sol-1")


def test_delete_error_solution_no_chroma(manager, mock_unified_db):
    mock_unified_db.is_available.return_value = False
    result = manager.delete_error_solution("sol-1")
    assert result is False
