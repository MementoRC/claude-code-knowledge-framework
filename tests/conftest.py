"""Test configuration and fixtures for UCKN framework."""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any

@pytest.fixture
def temp_knowledge_dir() -> Generator[str, None, None]:
    """Create a temporary directory for knowledge storage."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def sample_patterns() -> list[Dict[str, Any]]:
    """Sample patterns for testing."""
    return [
        {
            "id": "test-pattern-1",
            "title": "Test Pattern 1",
            "description": "A test pattern for benchmarking",
            "content": "def test_function():\n    pass",
            "language": "python",
            "tags": ["test", "python"],
            "metadata": {"complexity": "low", "size": "small"}
        },
        {
            "id": "test-pattern-2", 
            "title": "Test Pattern 2",
            "description": "Another test pattern for benchmarking",
            "content": "class TestClass:\n    def __init__(self):\n        self.value = 42",
            "language": "python",
            "tags": ["test", "class"],
            "metadata": {"complexity": "medium", "size": "medium"}
        }
    ]

@pytest.fixture
def large_text_sample() -> str:
    """Large text sample for performance testing."""
    return " ".join([f"This is sentence number {i} for testing performance." for i in range(1000)])