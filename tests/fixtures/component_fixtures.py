"""
Component initialization and atomic component suite fixtures for UCKN.

Provides:
- Component factory for integration/E2E tests
- Atomic component suite for integration testing
- Health check utilities
"""

import pytest


@pytest.fixture
def atomic_component_suite():
    """
    Returns a suite of atomic components for integration testing.
    """
    from src.uckn.core.atoms.semantic_search import SemanticSearch
    from src.uckn.core.atoms.tech_stack_detector import TechStackDetector
    from src.uckn.core.molecules.error_solution_manager import ErrorSolutionManager
    from src.uckn.core.molecules.pattern_classification import PatternClassification
    from src.uckn.core.molecules.pattern_manager import PatternManager
    from src.uckn.storage.chromadb_connector import ChromaDBConnector

    # Use dummy or real connectors as needed
    chroma = ChromaDBConnector(db_path=":memory:")
    semantic = SemanticSearch(knowledge_dir=":memory:")
    tech = TechStackDetector()
    # Create unified_db for PatternManager
    from tests.fixtures.database_fixtures import DummyUnifiedDatabase
    unified_db = DummyUnifiedDatabase()
    pattern_mgr = PatternManager(unified_db, semantic)
    error_mgr = ErrorSolutionManager(chroma, semantic)
    pattern_class = PatternClassification(chroma)

    return {
        "chroma_connector": chroma,
        "semantic_search": semantic,
        "tech_detector": tech,
        "pattern_manager": pattern_mgr,
        "error_solution_manager": error_mgr,
        "pattern_classification": pattern_class
    }

@pytest.fixture
def component_health_checker():
    """
    Utility to check health of all atomic components.
    """
    def checker(components):
        health = {}
        for name, comp in components.items():
            if hasattr(comp, "is_available"):
                try:
                    health[name] = comp.is_available()
                except Exception:
                    health[name] = False
            else:
                health[name] = None
        return health
    return checker
