"""Test configuration and fixtures for UCKN framework."""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any

# --- Modular fixture imports for robust, reusable test infrastructure ---

from .fixtures.pattern_fixtures import *
from .fixtures.error_fixtures import *
from .fixtures.tech_stack_fixtures import *
from .fixtures.database_fixtures import *
from .fixtures.component_fixtures import *

# --- Core temporary directory fixture ---

@pytest.fixture
def temp_knowledge_dir() -> Generator[str, None, None]:
    """
    Create a temporary directory for knowledge storage.
    Ensures cleanup after test.
    """
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

# --- Performance/large text sample ---

@pytest.fixture
def large_text_sample() -> str:
    """
    Large text sample for performance testing.
    """
    return " ".join([f"This is sentence number {i} for testing performance." for i in range(1000)])

# --- Health check utility for UCKN components ---

@pytest.fixture
def health_check_util():
    """
    Utility to check health of UCKN components.
    Returns a function that takes a component and returns its health status.
    """
    def check(component):
        if hasattr(component, "is_available"):
            try:
                return component.is_available()
            except Exception:
                return False
        return False
    return check

# --- Component factory for dependency injection and atomic suite ---

@pytest.fixture
def uckn_component_factory():
    """
    Factory for creating UCKN components with dependency injection.
    Supports custom configuration for integration and E2E tests.
    """
    from src.uckn.core.organisms.knowledge_manager import KnowledgeManager
    from src.uckn.core.atoms.semantic_search import SemanticSearch
    from src.uckn.core.atoms.tech_stack_detector import TechStackDetector
    from src.uckn.core.molecules.pattern_manager import PatternManager
    from src.uckn.core.molecules.error_solution_manager import ErrorSolutionManager
    from src.uckn.core.molecules.pattern_classification import PatternClassification
    from src.uckn.storage.chromadb_connector import ChromaDBConnector

    def factory(
        knowledge_dir=None,
        chroma_connector=None,
        semantic_search=None,
        tech_detector=None,
        pattern_manager=None,
        error_solution_manager=None,
        pattern_classification=None,
    ):
        # Use provided or default
        knowledge_dir = knowledge_dir or tempfile.mkdtemp()
        chroma_connector = chroma_connector or ChromaDBConnector(db_path=str(Path(knowledge_dir) / "chroma_db"))
        semantic_search = semantic_search or SemanticSearch(knowledge_dir=str(knowledge_dir))
        tech_detector = tech_detector or TechStackDetector()
        pattern_manager = pattern_manager or PatternManager(chroma_connector, semantic_search)
        error_solution_manager = error_solution_manager or ErrorSolutionManager(chroma_connector, semantic_search)
        pattern_classification = pattern_classification or PatternClassification(chroma_connector)
        # Compose KnowledgeManager with injected dependencies
        km = KnowledgeManager(knowledge_dir=knowledge_dir)
        km.chroma_connector = chroma_connector
        km.semantic_search = semantic_search
        km.tech_detector = tech_detector
        km.pattern_manager = pattern_manager
        km.error_solution_manager = error_solution_manager
        km.pattern_classification = pattern_classification
        return km

    return factory

# --- Async error simulation utility ---

@pytest.fixture
def async_error_simulator():
    """
    Utility to simulate async errors for resource exhaustion and network failures.
    """
    import asyncio

    class AsyncErrorSimulator:
        async def raise_timeout(self, delay=0.01):
            await asyncio.sleep(delay)
            raise asyncio.TimeoutError("Simulated async timeout")

        async def raise_network_error(self):
            raise ConnectionError("Simulated network failure")

        async def exhaust_resources(self):
            # Simulate resource exhaustion (memory)
            try:
                a = []
                for _ in range(10**7):
                    a.append("x" * 1024)
            except MemoryError:
                return True
            return False

    return AsyncErrorSimulator()

# --- General error scenario generator ---

@pytest.fixture
def error_scenario_generator():
    """
    Generates error scenarios for testing error handling.
    """
    def generator(error_type="generic", message="Simulated error"):
        if error_type == "network":
            raise ConnectionError(message)
        elif error_type == "timeout":
            import time
            time.sleep(0.1)
            raise TimeoutError(message)
        elif error_type == "resource":
            raise MemoryError(message)
        else:
            raise Exception(message)
    return generator
