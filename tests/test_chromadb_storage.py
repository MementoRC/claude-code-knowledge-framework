import os
import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the connector and ML environment manager
from src.uckn.storage.chromadb_connector import ChromaDBConnector
from src.uckn.core.ml_environment_manager import get_ml_manager


# Mock the SemanticSearchEngine for tests that don't need actual embeddings
# This is crucial because SemanticSearchEngine tries to load a model.
@pytest.fixture(autouse=True)
def mock_semantic_search_engine():
    with patch("uckn.core.SemanticSearchEngine") as MockEngine:
        mock_instance = MagicMock()
        mock_instance.is_available.return_value = True
        mock_instance.sentence_model = MagicMock()
        mock_instance.sentence_model.encode.return_value = [
            0.1
        ] * 384  # Example embedding
        MockEngine.return_value = mock_instance
        yield MockEngine


@pytest.fixture
def temp_db_path(tmp_path):
    """Provides a temporary directory for ChromaDB."""
    db_dir = tmp_path / "test_chroma_db"
    db_dir.mkdir()
    yield str(db_dir)
    # Clean up after test
    if db_dir.exists():
        shutil.rmtree(db_dir)


@pytest.fixture
def chroma_connector(temp_db_path):
    """Provides an initialized ChromaDBConnector instance."""
    connector = ChromaDBConnector(db_path=temp_db_path)
    # Ensure it's available before tests run, or skip if not
    if not connector.is_available():
        pytest.skip("ChromaDB is not available for testing.")
    yield connector
    # Clean up collections after each test
    if connector.is_available():
        connector.reset_db()


@pytest.mark.skipif(
    not get_ml_manager().capabilities.chromadb,
    reason="ChromaDB not available in current environment",
)
class TestChromaDBConnector:
    def test_initialization_and_availability(self, temp_db_path):
        connector = ChromaDBConnector(db_path=temp_db_path)
        assert connector.is_available()
        assert connector.client is not None
        assert "code_patterns" in connector.collections
        assert "error_solutions" in connector.collections

    @patch("uckn.storage.chromadb_connector.CHROMADB_AVAILABLE", False)
    def test_graceful_degradation_no_chromadb(self, temp_db_path):
        connector = ChromaDBConnector(db_path=temp_db_path)
        assert not connector.is_available()
        assert connector.client is None
        assert not connector.collections
        # Test that methods return False/empty/None gracefully
        assert not connector.add_document("code_patterns", "id1", "doc", [0.1], {})
        assert connector.get_document("code_patterns", "id1") is None
        assert not connector.update_document("code_patterns", "id1", document="new")
        assert not connector.delete_document("code_patterns", "id1")
        assert connector.search_documents("code_patterns", [0.1]) == []
        assert connector.count_documents("code_patterns") == 0
        assert not connector.reset_db()

    def test_add_document_code_patterns(self, chroma_connector):
        doc_id = "pattern_123"
        document = "Python CI setup with Poetry and Pytest"
        embedding = [0.1] * 384
        metadata = {
            "technology_stack": ["python", "poetry", "pytest"],
            "pattern_type": "ci_setup",
            "success_rate": 0.95,
            "pattern_id": doc_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        assert chroma_connector.add_document(
            "code_patterns", doc_id, document, embedding, metadata
        )
        assert chroma_connector.count_documents("code_patterns") == 1

        retrieved = chroma_connector.get_document("code_patterns", doc_id)
        assert retrieved is not None
        assert retrieved["id"] == doc_id
        assert retrieved["document"] == document
        assert retrieved["metadata"] == metadata
        assert retrieved["embedding"] == embedding

    def test_add_document_error_solutions(self, chroma_connector):
        doc_id = "error_sol_456"
        document = "Dependency conflict in requirements.txt"
        embedding = [0.2] * 384
        metadata = {
            "error_category": "dependency_conflict",
            "resolution_steps": ["update pip", "check constraints"],
            "avg_resolution_time": 20.5,
            "solution_id": doc_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        assert chroma_connector.add_document(
            "error_solutions", doc_id, document, embedding, metadata
        )
        assert chroma_connector.count_documents("error_solutions") == 1

        retrieved = chroma_connector.get_document("error_solutions", doc_id)
        assert retrieved is not None
        assert retrieved["id"] == doc_id
        assert retrieved["document"] == document
        assert retrieved["metadata"] == metadata
        assert retrieved["embedding"] == embedding

    def test_add_document_invalid_metadata(self, chroma_connector):
        doc_id = "invalid_pattern"
        document = "Some text"
        embedding = [0.3] * 384
        # Missing required key 'pattern_type'
        metadata = {
            "technology_stack": ["python"],
            "success_rate": 0.8,
            "pattern_id": doc_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        assert not chroma_connector.add_document(
            "code_patterns", doc_id, document, embedding, metadata
        )
        assert chroma_connector.count_documents("code_patterns") == 0

        # Incorrect type for 'success_rate'
        metadata_bad_type = {
            "technology_stack": ["python"],
            "pattern_type": "ci_setup",
            "success_rate": "high",  # Should be float
            "pattern_id": doc_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        assert not chroma_connector.add_document(
            "code_patterns", doc_id, document, embedding, metadata_bad_type
        )
        assert chroma_connector.count_documents("code_patterns") == 0

    def test_get_non_existent_document(self, chroma_connector):
        assert chroma_connector.get_document("code_patterns", "non_existent_id") is None

    def test_update_document(self, chroma_connector):
        doc_id = "pattern_to_update"
        document = "Initial document text"
        embedding = [0.1] * 384
        metadata = {
            "technology_stack": ["python"],
            "pattern_type": "test",
            "success_rate": 0.5,
            "pattern_id": doc_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        chroma_connector.add_document(
            "code_patterns", doc_id, document, embedding, metadata
        )

        new_document = "Updated document text"
        new_metadata = {"success_rate": 0.99, "technology_stack": ["python", "docker"]}
        assert chroma_connector.update_document(
            "code_patterns", doc_id, document=new_document, metadata=new_metadata
        )

        retrieved = chroma_connector.get_document("code_patterns", doc_id)
        assert retrieved["document"] == new_document
        assert retrieved["metadata"]["success_rate"] == 0.99
        assert retrieved["metadata"]["technology_stack"] == ["python", "docker"]
        assert (
            retrieved["metadata"]["updated_at"] != metadata["updated_at"]
        )  # Should be updated

    def test_delete_document(self, chroma_connector):
        doc_id = "pattern_to_delete"
        document = "Document to be deleted"
        embedding = [0.1] * 384
        metadata = {
            "technology_stack": ["python"],
            "pattern_type": "test",
            "success_rate": 0.5,
            "pattern_id": doc_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        chroma_connector.add_document(
            "code_patterns", doc_id, document, embedding, metadata
        )
        assert chroma_connector.count_documents("code_patterns") == 1

        assert chroma_connector.delete_document("code_patterns", doc_id)
        assert chroma_connector.count_documents("code_patterns") == 0
        assert chroma_connector.get_document("code_patterns", doc_id) is None

    def test_search_documents(self, chroma_connector):
        # Add a few documents for searching
        patterns_to_add = [
            {
                "id": "p1",
                "doc": "Python CI with GitHub Actions",
                "meta": {
                    "technology_stack": ["python", "github_actions"],
                    "pattern_type": "ci",
                    "success_rate": 0.9,
                    "pattern_id": "p1",
                    "created_at": "2023-01-01T00:00:00",
                    "updated_at": "2023-01-01T00:00:00",
                },
            },
            {
                "id": "p2",
                "doc": "Node.js deployment to AWS",
                "meta": {
                    "technology_stack": ["nodejs", "aws"],
                    "pattern_type": "deployment",
                    "success_rate": 0.8,
                    "pattern_id": "p2",
                    "created_at": "2023-01-02T00:00:00",
                    "updated_at": "2023-01-02T00:00:00",
                },
            },
            {
                "id": "p3",
                "doc": "Python testing with Pytest and Docker",
                "meta": {
                    "technology_stack": ["python", "pytest", "docker"],
                    "pattern_type": "testing",
                    "success_rate": 0.95,
                    "pattern_id": "p3",
                    "created_at": "2023-01-03T00:00:00",
                    "updated_at": "2023-01-03T00:00:00",
                },
            },
        ]
        for p in patterns_to_add:
            # Use a simple mock embedding for testing search logic, actual values don't matter for this test
            # as long as they are consistent and allow distance calculation.
            # For a real test, you'd need a proper embedding function or mock it to return specific distances.
            # Here, we'll just use a dummy embedding and rely on ChromaDB's internal distance.
            # To make search results predictable, we'll make query embedding similar to p1.
            embedding = [
                0.1 + (0.01 if p["id"] == "p1" else 0.05 if p["id"] == "p3" else 0.1)
            ] * 384
            chroma_connector.add_document(
                "code_patterns", p["id"], p["doc"], embedding, p["meta"]
            )

        # Mock query embedding to be very similar to p1
        query_embedding = [0.101] * 384  # Should be closest to p1

        results = chroma_connector.search_documents(
            "code_patterns", query_embedding, n_results=3, min_similarity=0.0
        )
        assert len(results) == 3  # All should be returned if min_similarity is 0

        # Check if results are sorted by similarity (highest first)
        # This depends on how ChromaDB calculates distance and how it's converted to similarity.
        # For L2 distance, smaller distance means higher similarity.
        # Our conversion is 1 / (1 + distance), so higher similarity means higher score.
        assert (
            results[0]["id"] == "p1" or results[0]["id"] == "p3"
        )  # p1 or p3 should be first depending on exact mock embedding
        assert results[0]["similarity_score"] >= results[1]["similarity_score"]
        assert results[1]["similarity_score"] >= results[2]["similarity_score"]

        # Test with metadata filter
        filtered_results = chroma_connector.search_documents(
            "code_patterns",
            query_embedding,
            n_results=3,
            min_similarity=0.0,
            where_clause={"pattern_type": "ci"},
        )
        assert len(filtered_results) == 1
        assert filtered_results[0]["id"] == "p1"

    def test_count_documents(self, chroma_connector):
        assert chroma_connector.count_documents("code_patterns") == 0
        chroma_connector.add_document(
            "code_patterns",
            "c1",
            "doc1",
            [0.1] * 384,
            {
                "technology_stack": ["py"],
                "pattern_type": "t",
                "success_rate": 0.5,
                "pattern_id": "c1",
                "created_at": "now",
                "updated_at": "now",
            },
        )
        assert chroma_connector.count_documents("code_patterns") == 1
        chroma_connector.add_document(
            "code_patterns",
            "c2",
            "doc2",
            [0.2] * 384,
            {
                "technology_stack": ["js"],
                "pattern_type": "t",
                "success_rate": 0.6,
                "pattern_id": "c2",
                "created_at": "now",
                "updated_at": "now",
            },
        )
        assert chroma_connector.count_documents("code_patterns") == 2

    def test_get_all_documents(self, chroma_connector):
        assert chroma_connector.get_all_documents("code_patterns") == []
        patterns_to_add = [
            {
                "id": "p1",
                "doc": "Python CI with GitHub Actions",
                "meta": {
                    "technology_stack": ["python", "github_actions"],
                    "pattern_type": "ci",
                    "success_rate": 0.9,
                    "pattern_id": "p1",
                    "created_at": "2023-01-01T00:00:00",
                    "updated_at": "2023-01-01T00:00:00",
                },
            },
            {
                "id": "p2",
                "doc": "Node.js deployment to AWS",
                "meta": {
                    "technology_stack": ["nodejs", "aws"],
                    "pattern_type": "deployment",
                    "success_rate": 0.8,
                    "pattern_id": "p2",
                    "created_at": "2023-01-02T00:00:00",
                    "updated_at": "2023-01-02T00:00:00",
                },
            },
        ]
        for p in patterns_to_add:
            chroma_connector.add_document(
                "code_patterns", p["id"], p["doc"], [0.1] * 384, p["meta"]
            )

        all_docs = chroma_connector.get_all_documents("code_patterns")
        assert len(all_docs) == 2
        ids = {d["id"] for d in all_docs}
        assert "p1" in ids
        assert "p2" in ids

    def test_reset_db(self, chroma_connector):
        chroma_connector.add_document(
            "code_patterns",
            "c1",
            "doc1",
            [0.1] * 384,
            {
                "technology_stack": ["py"],
                "pattern_type": "t",
                "success_rate": 0.5,
                "pattern_id": "c1",
                "created_at": "now",
                "updated_at": "now",
            },
        )
        chroma_connector.add_document(
            "error_solutions",
            "e1",
            "err1",
            [0.1] * 384,
            {
                "error_category": "dep",
                "resolution_steps": [],
                "avg_resolution_time": 10,
                "solution_id": "e1",
                "created_at": "now",
                "updated_at": "now",
            },
        )
        assert chroma_connector.count_documents("code_patterns") == 1
        assert chroma_connector.count_documents("error_solutions") == 1

        assert chroma_connector.reset_db()
        assert chroma_connector.count_documents("code_patterns") == 0
        assert chroma_connector.count_documents("error_solutions") == 0
