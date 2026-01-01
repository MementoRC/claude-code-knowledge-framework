
import pytest

from src.uckn.core.atoms.semantic_search_engine import SemanticSearchEngine


class DummyMultiModalEmbeddings:
    def __init__(self):
        self.calls = []

    def embed(self, data, data_type="auto"):
        self.calls.append((data, data_type))
        # Return a fixed vector for test
        return [1.0, 0.0, 0.0]

    def multi_modal_embed(self, text=None, code=None, error=None, **kwargs):
        self.calls.append(("multi", text, code, error))
        return [0.5, 0.5, 0.0]


class DummyChromaDBConnector:
    def __init__(self):
        self.last_query = None
        self.docs = {
            "code_patterns": [
                {
                    "id": "cp1",
                    "document": "pattern1",
                    "metadata": {"technology_stack": ["python"], "success_rate": 0.9},
                    "similarity_score": 0.95,
                },
                {
                    "id": "cp2",
                    "document": "pattern2",
                    "metadata": {"technology_stack": ["java"], "success_rate": 0.7},
                    "similarity_score": 0.8,
                },
                {
                    "id": "es1",
                    "document": "solution1",
                    "metadata": {
                        "technology_stack": ["python"],
                        "avg_resolution_time": 10,
                    },
                    "similarity_score": 0.92,
                },
            ],
            "error_solutions": [
                {
                    "id": "es1",
                    "document": "solution1",
                    "metadata": {
                        "technology_stack": ["python"],
                        "avg_resolution_time": 10,
                    },
                    "similarity_score": 0.92,
                }
            ],
        }

    def is_available(self):
        return True

    def search_documents(
        self, collection_name, query_embedding, n_results, min_similarity, where_clause
    ):
        self.last_query = (
            collection_name,
            query_embedding,
            n_results,
            min_similarity,
            where_clause,
        )
        # Return only docs with similarity >= min_similarity
        return [
            d
            for d in self.docs.get(collection_name, [])
            if d["similarity_score"] >= min_similarity
        ][:n_results]

    def query_collection(self, collection_name, query_embeddings, n_results, **kwargs):
        """ChromaDB-style query interface for the new API."""
        self.last_query = (collection_name, query_embeddings, n_results, kwargs)

        # Get documents from collection
        docs = self.docs.get(collection_name, [])

        # Simulate distance calculation (lower distance = higher similarity)
        results = {"ids": [[]], "distances": [[]], "documents": [[]], "metadatas": [[]]}

        for doc in docs[:n_results]:
            # Convert similarity to distance (distance = 1 - similarity)
            distance = 1.0 - doc["similarity_score"]

            results["ids"][0].append(doc["id"])
            results["distances"][0].append(distance)
            results["documents"][0].append(doc["document"])
            results["metadatas"][0].append(doc["metadata"])

        return results


@pytest.fixture
def engine():
    embeddings = DummyMultiModalEmbeddings()
    chroma = DummyChromaDBConnector()
    return SemanticSearchEngine(
        chroma_connector=chroma, embedding_atom=embeddings, cache_size=8
    )


def test_search_by_text_basic(engine):
    results = engine.search_by_text(
        "find a python pattern", tech_stack="python", limit=5
    )
    assert results
    assert results[0]["id"] == "cp1"
    assert results[0]["_tech_stack_score"] == 1.0
    assert results[0]["_success_score"] == 0.9


def test_search_by_code_basic(engine):
    results = engine.search_by_code("def foo(): pass", tech_stack=["python"], limit=5)
    assert results
    assert any(r["id"] == "cp1" for r in results)


def test_search_by_error_basic(engine):
    results = engine.search_by_error(
        "TypeError: NoneType", tech_stack="python", limit=5
    )
    assert results
    assert any(r["id"] == "es1" for r in results)


def test_search_multi_modal(engine):
    results = engine.search_multi_modal(
        text="foo", code="bar", error="baz", tech_stack="python", limit=5
    )
    assert results
    # Should call multi_modal_embed
    assert ("multi", "foo", "bar", "baz") in engine.embedding_atom.calls


def test_tech_stack_filtering(engine):
    # Only python stack should match
    results = engine.search_by_text("find a pattern", tech_stack="python", limit=5)
    assert all("python" in r["metadata"]["technology_stack"] for r in results)


def test_ranking_algorithm(engine):
    # cp1 has higher similarity and success_rate than cp2
    results = engine.search_by_text("find a pattern", tech_stack=None, limit=5)
    ids = [r["id"] for r in results]
    assert ids.index("cp1") < ids.index("cp2")


def test_caching(engine):
    # Call twice, should use cache for embedding
    engine.search_by_text("find a python pattern", tech_stack="python", limit=5)
    engine.search_by_text("find a python pattern", tech_stack="python", limit=5)
    # Only one embed call for same input
    calls = [c for c in engine.embedding_atom.calls if c[0] == "find a python pattern"]
    assert len(calls) == 1


def test_no_embedding_returns_empty(engine):
    # Patch embed to return None
    engine.embedding_atom.embed = lambda data, data_type="auto": None
    results = engine.search_by_text("foo", tech_stack="python", limit=5)
    assert results == []


def test_no_chromadb_returns_empty():
    # Patch chroma_connector to unavailable
    embeddings = DummyMultiModalEmbeddings()
    chroma = DummyChromaDBConnector()
    chroma.is_available = lambda: False
    engine = SemanticSearchEngine(
        chroma_connector=chroma, embedding_atom=embeddings, cache_size=8
    )
    results = engine.search_by_text("foo", tech_stack="python", limit=5)
    assert results == []


def test_error_handling(engine):
    # Patch chroma_connector to raise
    def fail_search(*a, **kw):
        raise Exception("fail")

    engine.chroma_connector.query_collection = fail_search
    results = engine.search_by_text("foo", tech_stack="python", limit=5)
    assert results == []
