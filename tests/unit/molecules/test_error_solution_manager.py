import pytest
from unittest.mock import MagicMock, patch, ANY

from src.uckn.core.molecules.error_solution_manager import ErrorSolutionManager
from src.uckn.storage import UnifiedDatabase # Import UnifiedDatabase

@pytest.fixture
def mock_unified_db(): # Renamed fixture
    db = MagicMock(spec=UnifiedDatabase) # Specify spec for better mock behavior
    db.is_available.return_value = True
    return db

@pytest.fixture
def mock_semantic_search():
    search = MagicMock()
    search.is_available.return_value = True
    return search

@pytest.fixture
def manager(mock_unified_db, mock_semantic_search): # Updated argument
    return ErrorSolutionManager(mock_unified_db, mock_semantic_search) # Updated constructor call

def test_initialization(mock_unified_db, mock_semantic_search): # Updated argument
    mgr = ErrorSolutionManager(mock_unified_db, mock_semantic_search) # Updated constructor call
    assert mgr.unified_db is mock_unified_db # Updated assertion
    assert mgr.semantic_search is mock_semantic_search

def test_add_error_solution_success(manager, mock_unified_db, mock_semantic_search): # Updated argument
    mock_semantic_search.encode.return_value = [0.1, 0.2, 0.3]
    mock_unified_db.add_error_solution.return_value = True # Updated mock method
    data = {"document": "error msg", "metadata": {"foo": "bar"}}
    result = manager.add_error_solution(data)
    assert result is not None
    mock_semantic_search.encode.assert_called_once_with("error msg")
    mock_unified_db.add_error_solution.assert_called_once_with( # Updated assertion with correct arguments
        document_text="error msg",
        embedding=[0.1, 0.2, 0.3],
        metadata={"foo": "bar", "solution_id": ANY, "created_at": ANY, "updated_at": ANY},
        solution_id=ANY,
        project_id=None
    )

def test_add_error_solution_no_chroma(manager, mock_unified_db): # Updated argument
    mock_unified_db.is_available.return_value = False # Updated mock object
    result = manager.add_error_solution({"document": "err"})
    assert result is None

def test_add_error_solution_no_semantic(manager, mock_semantic_search):
    mock_semantic_search.is_available.return_value = False
    # Updated constructor call with MagicMock() for unified_db
    result = ErrorSolutionManager(MagicMock(spec=UnifiedDatabase), mock_semantic_search).add_error_solution({"document": "err"})
    assert result is None

def test_add_error_solution_no_document(manager):
    result = manager.add_error_solution({"metadata": {}})
    assert result is None

def test_add_error_solution_embedding_fail(manager, mock_semantic_search):
    mock_semantic_search.encode.return_value = None
    result = manager.add_error_solution({"document": "err"})
    assert result is None

def test_get_error_solution_success(manager, mock_unified_db): # Updated argument
    mock_unified_db.get_error_solution.return_value = {"id": "sol-1"} # Updated mock method
    result = manager.get_error_solution("sol-1")
    assert result == {"id": "sol-1"}
    mock_unified_db.get_error_solution.assert_called_once_with("sol-1") # Updated assertion

def test_get_error_solution_no_chroma(manager, mock_unified_db): # Updated argument
    mock_unified_db.is_available.return_value = False # Updated mock object
    result = manager.get_error_solution("sol-1")
    assert result is None

def test_search_error_solutions_success(manager, mock_unified_db, mock_semantic_search): # Updated argument
    mock_semantic_search.encode.return_value = [0.1, 0.2, 0.3]
    mock_unified_db.search_error_solutions.return_value = [{"id": "sol-1"}] # Updated mock method
    result = manager.search_error_solutions("err", limit=5, min_similarity=0.8, metadata_filter={"foo": "bar"})
    assert result == [{"id": "sol-1"}]
    mock_semantic_search.encode.assert_called_once_with("err")
    mock_unified_db.search_error_solutions.assert_called_once_with( # Updated assertion with correct arguments
        query_embedding=[0.1, 0.2, 0.3],
        n_results=5,
        min_similarity=0.8,
        metadata_filter={"foo": "bar"}
    )

def test_search_error_solutions_no_chroma(manager, mock_unified_db): # Updated argument
    mock_unified_db.is_available.return_value = False # Updated mock object
    result = manager.search_error_solutions("err")
    assert result == []

def test_search_error_solutions_no_semantic(manager, mock_semantic_search):
    mock_semantic_search.is_available.return_value = False
    # Updated constructor call with MagicMock() for unified_db
    result = ErrorSolutionManager(MagicMock(spec=UnifiedDatabase), mock_semantic_search).search_error_solutions("err")
    assert result == []

def test_search_error_solutions_embedding_fail(manager, mock_semantic_search):
    mock_semantic_search.encode.return_value = None
    result = manager.search_error_solutions("err")
    assert result == []

def test_update_error_solution_success(manager, mock_unified_db, mock_semantic_search): # Updated argument
    mock_unified_db.update_error_solution.return_value = True # Updated mock method
    mock_semantic_search.encode.return_value = [0.1, 0.2, 0.3]
    updates = {"document": "new doc", "metadata": {"foo": "bar"}}
    result = manager.update_error_solution("sol-1", updates)
    assert result is True
    mock_semantic_search.encode.assert_called_once_with("new doc")
    mock_unified_db.update_error_solution.assert_called_once_with( # Updated assertion with correct arguments
        solution_id="sol-1",
        document_text="new doc",
        embedding=[0.1, 0.2, 0.3],
        metadata={"foo": "bar", "updated_at": ANY},
        project_id=None
    )

def test_update_error_solution_no_chroma(manager, mock_unified_db): # Updated argument
    mock_unified_db.is_available.return_value = False # Updated mock object
    result = manager.update_error_solution("sol-1", {"document": "doc"})
    assert result is False

def test_update_error_solution_no_semantic(manager, mock_semantic_search, mock_unified_db): # Updated argument
    mock_semantic_search.is_available.return_value = False
    updates = {"document": "new doc"}
    # Updated constructor call
    manager = ErrorSolutionManager(mock_unified_db, mock_semantic_search)
    mock_unified_db.update_error_solution.return_value = True # Updated mock method
    result = manager.update_error_solution("sol-1", updates)
    assert result is True
    mock_unified_db.update_error_solution.assert_called_once_with( # Updated assertion
        solution_id="sol-1",
        document_text="new doc",
        embedding=None, # Embedding should be None if semantic search is unavailable
        metadata={"updated_at": ANY}, # Only updated_at is added if metadata is not explicitly provided in updates
        project_id=None
    )
    # encode should not be called

def test_update_error_solution_embedding_fail(manager, mock_semantic_search):
    mock_semantic_search.encode.return_value = None
    updates = {"document": "new doc"}
    result = manager.update_error_solution("sol-1", updates)
    assert result is False

def test_update_error_solution_metadata_only(manager, mock_unified_db): # Updated argument
    mock_unified_db.update_error_solution.return_value = True # Updated mock method
    updates = {"metadata": {"foo": "bar"}}
    result = manager.update_error_solution("sol-1", updates)
    assert result is True
    mock_unified_db.update_error_solution.assert_called_once_with( # Updated assertion
        solution_id="sol-1",
        document_text=None,
        embedding=None,
        metadata={"foo": "bar", "updated_at": ANY},
        project_id=None
    )

def test_delete_error_solution_success(manager, mock_unified_db): # Updated argument
    mock_unified_db.delete_error_solution.return_value = True # Updated mock method
    result = manager.delete_error_solution("sol-1")
    assert result is True
    mock_unified_db.delete_error_solution.assert_called_once_with("sol-1") # Updated assertion

def test_delete_error_solution_no_chroma(manager, mock_unified_db): # Updated argument
    mock_unified_db.is_available.return_value = False # Updated mock object
    result = manager.delete_error_solution("sol-1")
    assert result is False
