import pytest
from unittest.mock import MagicMock, patch

from src.uckn.core.molecules.error_solution_manager import ErrorSolutionManager

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
def manager(mock_chroma, mock_semantic_search):
    return ErrorSolutionManager(mock_chroma, mock_semantic_search)

def test_initialization(mock_chroma, mock_semantic_search):
    mgr = ErrorSolutionManager(mock_chroma, mock_semantic_search)
    assert mgr.chroma_connector is mock_chroma
    assert mgr.semantic_search is mock_semantic_search

def test_add_error_solution_success(manager, mock_chroma, mock_semantic_search):
    mock_semantic_search.encode.return_value = [0.1, 0.2, 0.3]
    mock_chroma.add_document.return_value = True
    data = {"document": "error msg", "metadata": {"foo": "bar"}}
    result = manager.add_error_solution(data)
    assert result is not None
    mock_chroma.add_document.assert_called_once()
    mock_semantic_search.encode.assert_called_once_with("error msg")

def test_add_error_solution_no_chroma(manager, mock_chroma):
    mock_chroma.is_available.return_value = False
    result = manager.add_error_solution({"document": "err"})
    assert result is None

def test_add_error_solution_no_semantic(manager, mock_semantic_search):
    mock_semantic_search.is_available.return_value = False
    result = ErrorSolutionManager(MagicMock(), mock_semantic_search).add_error_solution({"document": "err"})
    assert result is None

def test_add_error_solution_no_document(manager):
    result = manager.add_error_solution({"metadata": {}})
    assert result is None

def test_add_error_solution_embedding_fail(manager, mock_semantic_search):
    mock_semantic_search.encode.return_value = None
    result = manager.add_error_solution({"document": "err"})
    assert result is None

def test_get_error_solution_success(manager, mock_chroma):
    mock_chroma.get_document.return_value = {"id": "sol-1"}
    result = manager.get_error_solution("sol-1")
    assert result == {"id": "sol-1"}
    mock_chroma.get_document.assert_called_once_with(collection_name="error_solutions", doc_id="sol-1")

def test_get_error_solution_no_chroma(manager, mock_chroma):
    mock_chroma.is_available.return_value = False
    result = manager.get_error_solution("sol-1")
    assert result is None

def test_search_error_solutions_success(manager, mock_chroma, mock_semantic_search):
    mock_semantic_search.encode.return_value = [0.1, 0.2, 0.3]
    mock_chroma.search_documents.return_value = [{"id": "sol-1"}]
    result = manager.search_error_solutions("err", limit=5, min_similarity=0.8, metadata_filter={"foo": "bar"})
    assert result == [{"id": "sol-1"}]
    mock_chroma.search_documents.assert_called_once()
    mock_semantic_search.encode.assert_called_once_with("err")

def test_search_error_solutions_no_chroma(manager, mock_chroma):
    mock_chroma.is_available.return_value = False
    result = manager.search_error_solutions("err")
    assert result == []

def test_search_error_solutions_no_semantic(manager, mock_semantic_search):
    mock_semantic_search.is_available.return_value = False
    result = ErrorSolutionManager(MagicMock(), mock_semantic_search).search_error_solutions("err")
    assert result == []

def test_search_error_solutions_embedding_fail(manager, mock_semantic_search):
    mock_semantic_search.encode.return_value = None
    result = manager.search_error_solutions("err")
    assert result == []

def test_update_error_solution_success(manager, mock_chroma, mock_semantic_search):
    mock_chroma.update_document.return_value = True
    mock_semantic_search.encode.return_value = [0.1, 0.2, 0.3]
    updates = {"document": "new doc", "metadata": {"foo": "bar"}}
    result = manager.update_error_solution("sol-1", updates)
    assert result is True
    mock_chroma.update_document.assert_called_once()
    mock_semantic_search.encode.assert_called_once_with("new doc")

def test_update_error_solution_no_chroma(manager, mock_chroma):
    mock_chroma.is_available.return_value = False
    result = manager.update_error_solution("sol-1", {"document": "doc"})
    assert result is False

def test_update_error_solution_no_semantic(manager, mock_semantic_search, mock_chroma):
    mock_semantic_search.is_available.return_value = False
    updates = {"document": "new doc"}
    # Should warn but still call update_document with embedding=None
    manager = ErrorSolutionManager(mock_chroma, mock_semantic_search)
    mock_chroma.update_document.return_value = True
    result = manager.update_error_solution("sol-1", updates)
    assert result is True
    mock_chroma.update_document.assert_called_once()
    # encode should not be called

def test_update_error_solution_embedding_fail(manager, mock_semantic_search):
    mock_semantic_search.encode.return_value = None
    updates = {"document": "new doc"}
    result = manager.update_error_solution("sol-1", updates)
    assert result is False

def test_update_error_solution_metadata_only(manager, mock_chroma):
    mock_chroma.update_document.return_value = True
    updates = {"metadata": {"foo": "bar"}}
    result = manager.update_error_solution("sol-1", updates)
    assert result is True
    mock_chroma.update_document.assert_called_once()

def test_delete_error_solution_success(manager, mock_chroma):
    mock_chroma.delete_document.return_value = True
    result = manager.delete_error_solution("sol-1")
    assert result is True
    mock_chroma.delete_document.assert_called_once_with(collection_name="error_solutions", doc_id="sol-1")

def test_delete_error_solution_no_chroma(manager, mock_chroma):
    mock_chroma.is_available.return_value = False
    result = manager.delete_error_solution("sol-1")
    assert result is False
