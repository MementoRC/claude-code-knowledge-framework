"""
Pattern management test fixtures for UCKN.

Provides:
- Sample patterns (various types, languages, and metadata)
- Pattern lifecycle helpers
- Semantic similarity validation pairs
- Pattern analytics datasets
"""

import pytest
import copy
from datetime import datetime, timedelta

@pytest.fixture
def sample_patterns() -> list:
    """
    Returns a list of sample patterns for testing.
    """
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
        },
        {
            "id": "test-pattern-3",
            "title": "Singleton Pattern",
            "description": "Ensure a class has only one instance.",
            "content": "class Singleton:\n    _instance = None\n    def __new__(cls):\n        if not cls._instance:\n            cls._instance = super().__new__(cls)\n        return cls._instance",
            "language": "python",
            "tags": ["singleton", "design-pattern"],
            "metadata": {"complexity": "medium", "size": "small"}
        }
    ]

@pytest.fixture
def pattern_lifecycle_helper():
    """
    Helper for pattern lifecycle management (add, update, delete).
    """
    class PatternLifecycle:
        def __init__(self):
            self.patterns = {}

        def add(self, pattern):
            self.patterns[pattern["id"]] = copy.deepcopy(pattern)
            return pattern["id"]

        def update(self, pattern_id, updates):
            if pattern_id in self.patterns:
                self.patterns[pattern_id].update(updates)
                return True
            return False

        def delete(self, pattern_id):
            if pattern_id in self.patterns:
                del self.patterns[pattern_id]
                return True
            return False

        def get(self, pattern_id):
            return self.patterns.get(pattern_id)

    return PatternLifecycle()

@pytest.fixture
def semantic_similarity_pairs():
    """
    Returns pairs of patterns and queries for semantic similarity validation.
    """
    return [
        ("singleton", "class Singleton:\n    _instance = None\n    def __new__(cls):\n        if not cls._instance:\n            cls._instance = super().__new__(cls)\n        return cls._instance"),
        ("test function", "def test_function():\n    pass"),
        ("class with value", "class TestClass:\n    def __init__(self):\n        self.value = 42"),
    ]

@pytest.fixture
def pattern_analytics_dataset():
    """
    Returns a dataset for pattern analytics (e.g., usage, success rate over time).
    """
    now = datetime.utcnow()
    return [
        {
            "pattern_id": "test-pattern-1",
            "usage_count": 10,
            "success_rate": 0.9,
            "last_used": (now - timedelta(days=1)).isoformat()
        },
        {
            "pattern_id": "test-pattern-2",
            "usage_count": 5,
            "success_rate": 0.8,
            "last_used": (now - timedelta(days=2)).isoformat()
        }
    ]
