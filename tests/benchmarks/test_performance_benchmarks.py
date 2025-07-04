"""
Performance benchmark tests for UCKN framework.

Uses pytest-benchmark to measure performance of key operations
and establish baseline metrics for performance regression detection.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any
import time
import gc

# Import core components for benchmarking
from uckn.core.atoms.multi_modal_embeddings import MultiModalEmbeddings
from uckn.core.atoms.semantic_search_engine import SemanticSearchEngine
from uckn.storage.chromadb_connector import ChromaDBConnector
from uckn.core.organisms.knowledge_manager import KnowledgeManager


class TestEmbeddingPerformance:
    """Benchmark tests for embedding generation performance."""

    @pytest.fixture
    def embeddings(self, temp_knowledge_dir):
        """Create MultiModalEmbeddings instance for testing."""
        return MultiModalEmbeddings()

    @pytest.fixture
    def test_texts(self):
        """Various sized text samples for benchmarking."""
        return {
            "small": "def hello(): return 'world'",
            "medium": "class DatabaseConnector:\n    def __init__(self, host, port):\n        self.host = host\n        self.port = port\n    def connect(self):\n        return f'Connecting to {self.host}:{self.port}'",
            "large": "\n".join([f"# Line {i}: This is a comprehensive code example" for i in range(100)]) + 
                    "\nclass LargeClass:\n    def method_" + "\n    def method_".join([f"{i}(self): pass" for i in range(50)])
        }

    def test_single_text_embedding_performance(self, benchmark, embeddings, test_texts):
        """Benchmark single text embedding generation."""
        if not embeddings.is_available():
            pytest.skip("Embeddings not available")
            
        result = benchmark(embeddings.embed, test_texts["medium"], "text")
        assert result is not None
        assert len(result) > 0

    def test_batch_embedding_performance(self, benchmark, embeddings, test_texts):
        """Benchmark batch embedding generation."""
        if not embeddings.is_available():
            pytest.skip("Embeddings not available")
            
        texts = [test_texts["small"], test_texts["medium"], test_texts["large"]]
        
        def batch_embed():
            return embeddings.embed_batch(texts, ["text"] * len(texts))
            
        result = benchmark(batch_embed)
        assert result is not None
        assert len(result) == len(texts)

    def test_code_embedding_performance(self, benchmark, embeddings, test_texts):
        """Benchmark code-specific embedding generation."""
        if not embeddings.is_available():
            pytest.skip("Embeddings not available")
            
        result = benchmark(embeddings.embed, test_texts["medium"], "code")
        assert result is not None

    def test_multi_modal_embedding_performance(self, benchmark, embeddings, test_texts):
        """Benchmark multi-modal embedding generation."""
        if not embeddings.is_available():
            pytest.skip("Embeddings not available")
            
        data = {
            "text": test_texts["medium"],
            "code": test_texts["small"],
            "config": "debug = True\nverbose = False"
        }
        
        result = benchmark(embeddings.multi_modal_embed, code=data["code"], text=data["text"], config=data["config"])
        assert result is not None

    @pytest.mark.parametrize("cache_size", [10, 50, 100])
    def test_embedding_cache_performance(self, benchmark, temp_knowledge_dir, test_texts, cache_size):
        """Benchmark embedding cache performance with different cache sizes."""
        embeddings = MultiModalEmbeddings()
        if not embeddings.is_available():
            pytest.skip("Embeddings not available")
            
        # Pre-populate cache
        for i in range(cache_size // 2):
            embeddings.embed(f"cached text {i}", "text")
        
        def cached_embed():
            # Mix of cached and new embeddings
            embeddings.embed("cached text 0", "text")  # Should be cached
            embeddings.embed(f"new text {time.time()}", "text")  # Not cached
            
        benchmark(cached_embed)


class TestSearchPerformance:
    """Benchmark tests for semantic search performance."""

    @pytest.fixture
    def search_engine(self, temp_knowledge_dir):
        """Create SemanticSearchEngine instance for testing."""
        return SemanticSearchEngine(knowledge_dir=temp_knowledge_dir)

    @pytest.fixture
    def populated_search_engine(self, search_engine, sample_patterns):
        """Search engine with pre-populated patterns."""
        if not search_engine.is_available():
            pytest.skip("Search engine not available")
            
        # Add sample patterns
        for pattern in sample_patterns:
            search_engine.chroma_connector.add_document(
                collection_name="code_patterns",
                doc_id=pattern["id"],
                content=pattern["content"],
                metadata=pattern.get("metadata", {})
            )
        return search_engine

    def test_text_search_performance(self, benchmark, populated_search_engine):
        """Benchmark text-based search performance."""
        if not populated_search_engine.is_available():
            pytest.skip("Search engine not available")
            
        result = benchmark(
            populated_search_engine.search_by_text,
            "test function",
            max_results=10
        )
        assert isinstance(result, list)

    def test_code_search_performance(self, benchmark, populated_search_engine):
        """Benchmark code-based search performance."""
        if not populated_search_engine.is_available():
            pytest.skip("Search engine not available")
            
        result = benchmark(
            populated_search_engine.search_by_code,
            "def test():",
            max_results=10
        )
        assert isinstance(result, list)

    def test_multi_modal_search_performance(self, benchmark, populated_search_engine):
        """Benchmark multi-modal search performance."""
        if not populated_search_engine.is_available():
            pytest.skip("Search engine not available")
            
        search_data = {
            "text": "test functionality",
            "code": "def test():",
            "tech_stack": ["python"]
        }
        
        result = benchmark(
            populated_search_engine.search_multi_modal,
            search_data,
            max_results=10
        )
        assert isinstance(result, list)

    @pytest.mark.parametrize("result_count", [5, 10, 25, 50])
    def test_search_scaling_performance(self, benchmark, populated_search_engine, result_count):
        """Benchmark search performance with different result counts."""
        if not populated_search_engine.is_available():
            pytest.skip("Search engine not available")
            
        result = benchmark(
            populated_search_engine.search_by_text,
            "test pattern",
            max_results=result_count
        )
        assert isinstance(result, list)


class TestStoragePerformance:
    """Benchmark tests for ChromaDB storage performance."""

    @pytest.fixture
    def storage(self, temp_knowledge_dir):
        """Create ChromaDBConnector instance for testing."""
        return ChromaDBConnector(db_path=str(Path(temp_knowledge_dir) / "chroma_db"))

    def test_document_insertion_performance(self, benchmark, storage, sample_patterns):
        """Benchmark single document insertion performance."""
        if not storage.is_available():
            pytest.skip("ChromaDB not available")
            
        pattern = sample_patterns[0]
        
        def insert_document():
            doc_id = f"perf_test_{time.time()}"
            return storage.add_document(
                collection_name="test_collection",
                doc_id=doc_id,
                content=pattern["content"],
                metadata=pattern.get("metadata", {})
            )
            
        result = benchmark(insert_document)
        assert result is True

    def test_bulk_insertion_performance(self, benchmark, storage, sample_patterns):
        """Benchmark bulk document insertion performance."""
        if not storage.is_available():
            pytest.skip("ChromaDB not available")
            
        def bulk_insert():
            for i, pattern in enumerate(sample_patterns * 10):  # 20 documents
                storage.add_document(
                    collection_name="bulk_test",
                    doc_id=f"bulk_{i}_{time.time()}",
                    content=pattern["content"],
                    metadata=pattern.get("metadata", {})
                )
                
        benchmark(bulk_insert)

    def test_search_performance_by_size(self, benchmark, storage, sample_patterns):
        """Benchmark search performance with different database sizes."""
        if not storage.is_available():
            pytest.skip("ChromaDB not available")
            
        # Pre-populate with documents
        for i, pattern in enumerate(sample_patterns * 25):  # 50 documents
            storage.add_document(
                collection_name="size_test",
                doc_id=f"size_test_{i}",
                content=pattern["content"],
                metadata=pattern.get("metadata", {})
            )
        
        def search_documents():
            return storage.search_documents(
                collection_name="size_test",
                query_text="test function",
                max_results=10
            )
            
        result = benchmark(search_documents)
        assert isinstance(result, list)

    def test_metadata_filtering_performance(self, benchmark, storage, sample_patterns):
        """Benchmark search with metadata filtering performance."""
        if not storage.is_available():
            pytest.skip("ChromaDB not available")
            
        # Pre-populate with documents
        for i, pattern in enumerate(sample_patterns * 10):
            metadata = pattern.get("metadata", {}).copy()
            metadata["test_id"] = i % 3  # Create filterable metadata
            storage.add_document(
                collection_name="filter_test",
                doc_id=f"filter_test_{i}",
                content=pattern["content"],
                metadata=metadata
            )
        
        def filtered_search():
            return storage.search_documents(
                collection_name="filter_test",
                query_text="test",
                max_results=10,
                where={"test_id": 1}
            )
            
        result = benchmark(filtered_search)
        assert isinstance(result, list)


class TestEndToEndPerformance:
    """Benchmark tests for end-to-end workflow performance."""

    @pytest.fixture
    def knowledge_manager(self, temp_knowledge_dir):
        """Create KnowledgeManager instance for testing."""
        return KnowledgeManager(knowledge_dir=temp_knowledge_dir)

    def test_pattern_addition_workflow(self, benchmark, knowledge_manager, sample_patterns):
        """Benchmark complete pattern addition workflow."""
        if not knowledge_manager.semantic_search.is_available():
            pytest.skip("Knowledge manager not available")
            
        pattern = sample_patterns[0]
        
        def add_pattern():
            return knowledge_manager.add_pattern(pattern)
            
        result = benchmark(add_pattern)
        assert result is not None

    def test_pattern_search_workflow(self, benchmark, knowledge_manager, sample_patterns):
        """Benchmark complete pattern search workflow."""
        if not knowledge_manager.semantic_search.is_available():
            pytest.skip("Knowledge manager not available")
            
        # Pre-populate
        for pattern in sample_patterns:
            knowledge_manager.add_pattern(pattern)
        
        def search_patterns():
            return knowledge_manager.search_patterns(
                query="test function",
                max_results=5
            )
            
        result = benchmark(search_patterns)
        assert isinstance(result, list)

    def test_tech_stack_analysis_performance(self, benchmark, knowledge_manager, temp_knowledge_dir):
        """Benchmark technology stack analysis performance."""
        # Create sample project structure
        project_dir = Path(temp_knowledge_dir) / "sample_project"
        project_dir.mkdir()
        
        # Create sample files
        (project_dir / "main.py").write_text("import pandas as pd\nprint('Hello')")
        (project_dir / "requirements.txt").write_text("pandas>=1.0.0\nnumpy>=1.20.0")
        (project_dir / "setup.py").write_text("from setuptools import setup")
        
        def analyze_stack():
            return knowledge_manager.analyze_project_stack(str(project_dir))
            
        result = benchmark(analyze_stack)
        assert isinstance(result, dict)


class TestMemoryPerformance:
    """Memory usage benchmark tests."""

    def test_embedding_memory_usage(self, temp_knowledge_dir, large_text_sample):
        """Test memory usage during embedding generation."""
        embeddings = MultiModalEmbeddings()
        if not embeddings.is_available():
            pytest.skip("Embeddings not available")
            
        # Force garbage collection before measurement
        gc.collect()
        
        # Generate embeddings for large text
        result = embeddings.embed(large_text_sample, "text")
        assert result is not None
        
        # Test batch processing memory
        batch_texts = [large_text_sample[:len(large_text_sample)//4] for _ in range(10)]
        batch_result = embeddings.embed_batch(batch_texts, ["text"] * len(batch_texts))
        assert len(batch_result) == len(batch_texts)

    def test_storage_memory_scaling(self, temp_knowledge_dir, sample_patterns):
        """Test memory usage scaling with database size."""
        storage = ChromaDBConnector(db_path=str(Path(temp_knowledge_dir) / "memory_test"))
        if not storage.is_available():
            pytest.skip("ChromaDB not available")
            
        # Add many documents and measure memory impact
        for i in range(100):
            for j, pattern in enumerate(sample_patterns):
                storage.add_document(
                    collection_name="memory_test",
                    doc_id=f"mem_test_{i}_{j}",
                    content=pattern["content"],
                    metadata=pattern.get("metadata", {})
                )
        
        # Perform searches to test memory during operations
        results = storage.search_documents(
            collection_name="memory_test",
            query_text="test",
            max_results=50
        )
        assert len(results) > 0
@pytest.mark.benchmark(group="embeddings")
class TestEmbeddingBenchmarkGroup:
    """Grouped benchmark tests for embeddings."""
    pass


@pytest.mark.benchmark(group="search") 
class TestSearchBenchmarkGroup:
    """Grouped benchmark tests for search operations."""
    pass


@pytest.mark.benchmark(group="storage")
class TestStorageBenchmarkGroup:
    """Grouped benchmark tests for storage operations."""
    pass


@pytest.mark.benchmark(group="end_to_end")
class TestEndToEndBenchmarkGroup:
    """Grouped benchmark tests for complete workflows."""
    pass

