import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.uckn.storage.chromadb_connector import ChromaDBConnector
from src.uckn.storage.postgresql_connector import (
    CompatibilityMatrix,
    ErrorSolution,
    Pattern,
    PatternCategory,
    PatternCategoryLink,
    PostgreSQLConnector,
    Project,
    TeamAccess,
)
from src.uckn.storage.unified_database import UnifiedDatabase


# Mock the underlying connectors
@pytest.fixture
def mock_pg_connector():
    mock = Mock(spec=PostgreSQLConnector)
    mock.is_available.return_value = True
    mock.add_record.side_effect = lambda model, data: data.get("id") or str(
        uuid.uuid4()
    )
    mock.get_record.return_value = None  # Default to not found
    mock.update_record.return_value = True
    mock.delete_record.return_value = True
    mock.get_all_records.return_value = []
    mock.filter_records.return_value = []
    mock.add_pattern_to_category.return_value = True
    mock.remove_pattern_from_category.return_value = True
    mock.get_patterns_in_category.return_value = []
    mock.get_categories_for_pattern.return_value = []
    mock.reset_db.return_value = True
    return mock


@pytest.fixture
def mock_chroma_connector():
    mock = Mock(spec=ChromaDBConnector)
    mock.is_available.return_value = True
    mock.add_document.return_value = True
    mock.get_document.return_value = None  # Default to not found
    mock.update_document.return_value = True
    mock.delete_document.return_value = True
    mock.search_documents.return_value = []
    mock.reset_db.return_value = True
    return mock


@pytest.fixture
def unified_db(mock_pg_connector, mock_chroma_connector):
    # Create UnifiedDatabase and manually assign the mocks to avoid complex patching
    db = UnifiedDatabase.__new__(UnifiedDatabase)  # Create instance without __init__
    db.pg_connector = mock_pg_connector
    db.chroma_connector = mock_chroma_connector
    db._logger = Mock()
    return db


def test_unified_db_initialization(
    unified_db, mock_pg_connector, mock_chroma_connector
):
    assert unified_db.pg_connector is mock_pg_connector
    assert unified_db.chroma_connector is mock_chroma_connector
    # Test that the connectors are properly assigned (no initialization calls expected)


def test_is_available_both_up(unified_db, mock_pg_connector, mock_chroma_connector):
    mock_pg_connector.is_available.return_value = True
    mock_chroma_connector.is_available.return_value = True
    assert unified_db.is_available()


def test_is_available_pg_down(unified_db, mock_pg_connector, mock_chroma_connector):
    mock_pg_connector.is_available.return_value = False
    mock_chroma_connector.is_available.return_value = True
    assert not unified_db.is_available()


def test_is_available_chroma_down(unified_db, mock_pg_connector, mock_chroma_connector):
    mock_pg_connector.is_available.return_value = True
    mock_chroma_connector.is_available.return_value = False
    assert not unified_db.is_available()


def test_reset_db(unified_db, mock_pg_connector, mock_chroma_connector):
    assert unified_db.reset_db()
    mock_pg_connector.reset_db.assert_called_once()
    mock_chroma_connector.reset_db.assert_called_once()


# --- Project Management Tests ---
def test_add_project(unified_db, mock_pg_connector):
    project_id = unified_db.add_project("New Project", "Description")
    assert project_id is not None
    mock_pg_connector.add_record.assert_called_once_with(
        Project, {"id": project_id, "name": "New Project", "description": "Description"}
    )


def test_get_project(unified_db, mock_pg_connector):
    mock_pg_connector.get_record.return_value = {"id": "proj1", "name": "Test Project"}
    project = unified_db.get_project("proj1")
    assert project["name"] == "Test Project"
    mock_pg_connector.get_record.assert_called_once_with(Project, "proj1")


# --- Pattern Management Tests ---
def test_add_pattern_success(unified_db, mock_pg_connector, mock_chroma_connector):
    doc_text = "Test pattern document"
    embedding = [0.1] * 128
    metadata = {"tech": "Python", "pattern_type": "Creational"}

    pattern_id = unified_db.add_pattern(
        doc_text, embedding, metadata, project_id="proj123"
    )
    assert pattern_id is not None

    mock_pg_connector.add_record.assert_called_once()
    args, kwargs = mock_pg_connector.add_record.call_args
    assert args[0] is Pattern
    assert args[1]["id"] == pattern_id
    assert args[1]["document_text"] == doc_text
    assert args[1]["metadata_json"] == metadata
    assert args[1]["project_id"] == "proj123"
    assert args[1]["technology_stack"] == "Python"  # Specific fields extracted

    mock_chroma_connector.add_document.assert_called_once_with(
        collection_name="code_patterns",
        doc_id=pattern_id,
        document=doc_text,
        embedding=embedding,
        metadata=metadata,
    )


def test_add_pattern_pg_fail_chroma_not_called(
    unified_db, mock_pg_connector, mock_chroma_connector
):
    mock_pg_connector.add_record.return_value = None  # Simulate PG failure

    pattern_id = unified_db.add_pattern("doc", [0.1], {})
    assert pattern_id is None
    mock_pg_connector.add_record.assert_called_once()
    mock_chroma_connector.add_document.assert_not_called()


def test_add_pattern_chroma_fail_pg_rolled_back(
    unified_db, mock_pg_connector, mock_chroma_connector
):
    mock_chroma_connector.add_document.return_value = False  # Simulate Chroma failure

    pattern_id = unified_db.add_pattern("doc", [0.1], {})
    assert pattern_id is None
    mock_pg_connector.add_record.assert_called_once()
    mock_chroma_connector.add_document.assert_called_once()
    mock_pg_connector.delete_record.assert_called_once()  # Should attempt rollback


def test_get_pattern_success(unified_db, mock_pg_connector, mock_chroma_connector):
    test_id = "pat123"
    pg_data = {
        "id": test_id,
        "project_id": "proj1",
        "document_text": "PG doc",
        "metadata_json": {"tech": "Python", "pattern_type": "Creational"},
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    chroma_data = {
        "id": test_id,
        "document": "Chroma doc",
        "embedding": [0.2] * 128,
        "metadata": {"tech": "Python", "pattern_type": "Creational"},
    }
    mock_pg_connector.get_record.return_value = pg_data
    mock_chroma_connector.get_document.return_value = chroma_data

    result = unified_db.get_pattern(test_id)
    assert result is not None
    assert result["id"] == test_id
    assert result["document"] == "Chroma doc"  # Prioritize Chroma's document
    assert result["embedding"] == [0.2] * 128
    assert (
        result["metadata"] == pg_data["metadata_json"]
    )  # Prioritize PG's metadata_json
    mock_pg_connector.get_record.assert_called_once_with(Pattern, test_id)
    mock_chroma_connector.get_document.assert_called_once_with(
        collection_name="code_patterns", doc_id=test_id
    )


def test_update_pattern_success(unified_db, mock_pg_connector, mock_chroma_connector):
    test_id = "pat123"
    new_doc = "Updated document"
    new_embedding = [0.3] * 128
    new_metadata = {"tech": "Java", "pattern_type": "Structural", "success_rate": 0.8}

    updated = unified_db.update_pattern(
        test_id,
        document_text=new_doc,
        embedding=new_embedding,
        metadata=new_metadata,
        project_id="proj456",
    )
    assert updated

    mock_pg_connector.update_record.assert_called_once()
    pg_args, pg_kwargs = mock_pg_connector.update_record.call_args
    assert pg_args[0] is Pattern
    assert pg_args[1] == test_id
    assert pg_args[2]["document_text"] == new_doc
    assert pg_args[2]["metadata_json"] == new_metadata
    assert pg_args[2]["project_id"] == "proj456"
    assert pg_args[2]["technology_stack"] == "Java"  # Specific fields updated

    mock_chroma_connector.update_document.assert_called_once_with(
        collection_name="code_patterns",
        doc_id=test_id,
        document=new_doc,
        embedding=new_embedding,
        metadata=new_metadata,
    )


def test_delete_pattern_success(unified_db, mock_pg_connector, mock_chroma_connector):
    test_id = "pat123"
    assert unified_db.delete_pattern(test_id)
    mock_pg_connector.delete_record.assert_called_once_with(Pattern, test_id)
    mock_chroma_connector.delete_document.assert_called_once_with(
        collection_name="code_patterns", doc_id=test_id
    )


def test_search_patterns(unified_db, mock_pg_connector, mock_chroma_connector):
    query_embedding = [0.5] * 128
    chroma_results = [
        {"id": "pat1", "document": "Doc A", "similarity_score": 0.9},
        {"id": "pat2", "document": "Doc B", "similarity_score": 0.8},
    ]
    mock_chroma_connector.search_documents.return_value = chroma_results
    mock_pg_connector.get_record.side_effect = [
        {
            "id": "pat1",
            "document_text": "PG Doc A",
            "metadata_json": {"tech": "Python"},
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        },
        {
            "id": "pat2",
            "document_text": "PG Doc B",
            "metadata_json": {"tech": "Java"},
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        },
    ]

    results = unified_db.search_patterns(
        query_embedding,
        n_results=2,
        min_similarity=0.7,
        metadata_filter={"tech": "Python"},
    )
    assert len(results) == 2
    assert results[0]["id"] == "pat1"
    assert results[0]["document"] == "Doc A"  # Chroma's document
    assert results[0]["metadata"] == {"tech": "Python"}  # PG's metadata
    assert results[1]["id"] == "pat2"
    assert results[1]["metadata"] == {"tech": "Java"}

    mock_chroma_connector.search_documents.assert_called_once_with(
        collection_name="code_patterns",
        query_embeddings=[query_embedding],
        n_results=2,
        min_similarity=0.7,
        where_clause={"tech": "Python"},
    )
    assert mock_pg_connector.get_record.call_count == 2


# --- Error Solution Management Tests (similar to patterns) ---
def test_add_error_solution_success(
    unified_db, mock_pg_connector, mock_chroma_connector
):
    doc_text = "Error message"
    embedding = [0.1] * 128
    metadata = {"error_category": "Network", "resolution_steps": "Check firewall"}

    solution_id = unified_db.add_error_solution(
        doc_text, embedding, metadata, project_id="proj123"
    )
    assert solution_id is not None

    mock_pg_connector.add_record.assert_called_once()
    args, kwargs = mock_pg_connector.add_record.call_args
    assert args[0] is ErrorSolution
    assert args[1]["id"] == solution_id
    assert args[1]["document_text"] == doc_text
    assert args[1]["metadata_json"] == metadata
    assert args[1]["project_id"] == "proj123"
    assert args[1]["error_category"] == "Network"

    mock_chroma_connector.add_document.assert_called_once_with(
        collection_name="error_solutions",
        doc_id=solution_id,
        document=doc_text,
        embedding=embedding,
        metadata=metadata,
    )


# --- Pattern Category Management Tests ---
def test_add_category(unified_db, mock_pg_connector):
    category_id = unified_db.add_category("New Category", "Description")
    assert category_id is not None
    mock_pg_connector.add_record.assert_called_once_with(
        PatternCategory,
        {"id": category_id, "name": "New Category", "description": "Description"},
    )


def test_assign_pattern_to_category(unified_db, mock_pg_connector):
    # Mock get_pattern and get_category to return non-None, indicating existence
    mock_pg_connector.get_record.side_effect = [
        {
            "id": "pat1",
            "document_text": "doc",
            "metadata_json": {},
        },  # For get_pattern check
        {"id": "cat1", "name": "Category"},  # For get_category check
    ]
    assert unified_db.assign_pattern_to_category("pat1", "cat1")
    mock_pg_connector.add_pattern_to_category.assert_called_once_with("pat1", "cat1")


def test_get_patterns_by_category(unified_db, mock_pg_connector):
    mock_pg_connector.get_patterns_in_category.return_value = ["pat1", "pat2"]
    patterns = unified_db.get_patterns_by_category("cat1")
    assert patterns == ["pat1", "pat2"]
    mock_pg_connector.get_patterns_in_category.assert_called_once_with("cat1")


# --- Team Access Management Tests ---
def test_add_team_access(unified_db, mock_pg_connector):
    access_id = unified_db.add_team_access("user1", "proj1", "admin")
    assert access_id is not None
    mock_pg_connector.add_record.assert_called_once_with(
        TeamAccess,
        {"id": access_id, "user_id": "user1", "project_id": "proj1", "role": "admin"},
    )


# --- Compatibility Matrix Management Tests ---
def test_add_compatibility_entry(unified_db, mock_pg_connector):
    entry_id = unified_db.add_compatibility_entry("Python", "Django", 0.9)
    assert entry_id is not None
    mock_pg_connector.add_record.assert_called_once_with(
        CompatibilityMatrix,
        {
            "id": entry_id,
            "source_tech": "Python",
            "target_tech": "Django",
            "compatibility_score": 0.9,
            "notes": None,
        },
    )


def test_search_compatibility_entries(unified_db, mock_pg_connector):
    mock_pg_connector.filter_records.return_value = [
        {
            "id": "e1",
            "source_tech": "Python",
            "target_tech": "Django",
            "compatibility_score": 0.9,
        },
        {
            "id": "e2",
            "source_tech": "Python",
            "target_tech": "Flask",
            "compatibility_score": 0.8,
        },
    ]
    results = unified_db.search_compatibility_entries(
        source_tech="Python", min_score=0.85
    )
    assert len(results) == 1
    assert results[0]["id"] == "e1"
    mock_pg_connector.filter_records.assert_called_once_with(
        CompatibilityMatrix, {"source_tech": "Python"}
    )
