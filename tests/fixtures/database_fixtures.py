"""
Database/storage fixtures for UCKN tests.

Provides:
- ChromaDB mock connector with realistic test data
- Storage schema standardization
- Performance dataset fixtures
- Database state management helpers
"""

import pytest
import copy

class DummyChromaDBConnector:
    """
    A mock ChromaDBConnector for testing.
    """
    def __init__(self):
        self.collections = {
            "code_patterns": [],
            "error_solutions": []
        }
        self.added_docs = []

    def is_available(self):
        return True

    def add_document(self, collection_name, doc_id, document, embedding, metadata):
        doc = {
            "id": doc_id,
            "document": document,
            "embedding": embedding,
            "metadata": metadata
        }
        self.collections[collection_name].append(doc)
        self.added_docs.append(doc)
        return True

    def get_document(self, collection_name, doc_id):
        for doc in self.collections[collection_name]:
            if doc["id"] == doc_id:
                return doc
        return None

    def search_documents(self, collection_name, query_embedding, n_results=10, min_similarity=0.7, where_clause=None):
        # Return the first n_results docs for simplicity
        return self.collections[collection_name][:n_results]

    def count_documents(self, collection_name):
        return len(self.collections[collection_name])

    def reset_db(self):
        for k in self.collections:
            self.collections[k] = []
        self.added_docs = []
        return True

@pytest.fixture
def dummy_chromadb_connector():
    """
    Returns a dummy ChromaDBConnector for isolated storage testing.
    """
    return DummyChromaDBConnector()

@pytest.fixture
def performance_dataset():
    """
    Returns a large dataset for performance and scalability testing.
    """
    base_doc = {
        "id": "perf-doc-{}",
        "document": "Performance test document {}",
        "embedding": [0.1] * 384,
        "metadata": {"test": True}
    }
    return [
        {
            "id": base_doc["id"].format(i),
            "document": base_doc["document"].format(i),
            "embedding": [float(i % 10)] * 384,
            "metadata": {"test": True, "index": i}
        }
        for i in range(1000)
    ]

@pytest.fixture
def db_state_manager(dummy_chromadb_connector):
    """
    Helper for managing database state across test scenarios.
    """
    class DBStateManager:
        def __init__(self, connector):
            self.connector = connector
            self.snapshots = []

        def snapshot(self):
            self.snapshots.append(copy.deepcopy(self.connector.collections))

        def restore(self):
            if self.snapshots:
                self.connector.collections = self.snapshots.pop()
    return DBStateManager(dummy_chromadb_connector)
