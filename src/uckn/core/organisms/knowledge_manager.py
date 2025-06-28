"""
UCKN Knowledge Manager Organism
Main orchestrator for the knowledge management system
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from ..atoms.semantic_search import SemanticSearch
from ..atoms.tech_stack_detector import TechStackDetector
from ..molecules.pattern_manager import PatternManager
from ..molecules.error_solution_manager import ErrorSolutionManager
from ..molecules.pattern_classification import PatternClassification
from ...storage import ChromaDBConnector


class KnowledgeManager:
    """Core knowledge management system using ChromaDB for storage."""

    def __init__(self, knowledge_dir: str = ".uckn/knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger(__name__)

        # Initialize ChromaDB connector
        self.chroma_connector = ChromaDBConnector(db_path=str(self.knowledge_dir / "chroma_db"))
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB is not available. Knowledge storage and retrieval will be limited.")

        # Initialize Semantic Search for embeddings
        self.semantic_search = SemanticSearch(knowledge_dir=str(self.knowledge_dir))
        if not self.semantic_search.is_available():
            self._logger.warning("Semantic search model not available. Embeddings cannot be generated.")

        # Initialize molecules
        self.pattern_manager = PatternManager(self.chroma_connector, self.semantic_search)
        self.error_solution_manager = ErrorSolutionManager(self.chroma_connector, self.semantic_search)
        self.pattern_classification = PatternClassification(self.chroma_connector)
        
        # Initialize atoms
        self.tech_detector = TechStackDetector()

    # Pattern management methods
    def add_pattern(self, pattern_data: Dict[str, Any]) -> Optional[str]:
        """Add a new knowledge pattern."""
        return self.pattern_manager.add_pattern(pattern_data)

    def get_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific pattern."""
        return self.pattern_manager.get_pattern(pattern_id)

    def update_pattern(self, pattern_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing pattern."""
        return self.pattern_manager.update_pattern(pattern_id, updates)

    def delete_pattern(self, pattern_id: str) -> bool:
        """Delete a pattern."""
        return self.pattern_manager.delete_pattern(pattern_id)

    def search_patterns(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.7,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for knowledge patterns using semantic similarity."""
        return self.pattern_manager.search_patterns(query, limit, min_similarity, metadata_filter)

    # Pattern classification methods
    def create_category(self, name: str, description: str = "", category_id: Optional[str] = None) -> Optional[str]:
        """Create a new pattern category."""
        return self.pattern_classification.add_category(name, description, category_id)

    def get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific category."""
        return self.pattern_classification.get_category(category_id)

    def update_category(self, category_id: str, name: Optional[str] = None, description: Optional[str] = None) -> bool:
        """Update an existing category."""
        return self.pattern_classification.update_category(category_id, name, description)

    def delete_category(self, category_id: str) -> bool:
        """Delete a category."""
        return self.pattern_classification.delete_category(category_id)

    def assign_pattern_to_category(self, pattern_id: str, category_id: str) -> bool:
        """Assign a pattern to a category."""
        return self.pattern_classification.assign_pattern_to_category(pattern_id, category_id)

    def remove_pattern_from_category(self, pattern_id: str, category_id: str) -> bool:
        """Remove a pattern from a category."""
        return self.pattern_classification.remove_pattern_from_category(pattern_id, category_id)

    def get_patterns_by_category(self, category_id: str) -> List[str]:
        """Get all pattern IDs in a category."""
        return self.pattern_classification.get_patterns_in_category(category_id)

    def get_pattern_categories(self, pattern_id: str) -> List[Dict[str, Any]]:
        """Get all categories assigned to a pattern."""
        return self.pattern_classification.get_categories_for_pattern(pattern_id)

    # Error solution management methods
    def add_error_solution(self, solution_data: Dict[str, Any]) -> Optional[str]:
        """Add a new error solution."""
        return self.error_solution_manager.add_error_solution(solution_data)

    def get_error_solution(self, solution_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific error solution."""
        return self.error_solution_manager.get_error_solution(solution_id)

    def search_error_solutions(
        self,
        error_query: str,
        limit: int = 10,
        min_similarity: float = 0.7,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for error solutions using semantic similarity."""
        return self.error_solution_manager.search_error_solutions(error_query, limit, min_similarity, metadata_filter)

    # Tech stack analysis
    def analyze_project_stack(self, project_path: str) -> Dict[str, Any]:
        """Analyze project technology stack."""
        return self.tech_detector.analyze_project(project_path)

    # Health and utility methods
    def get_health_status(self) -> Dict[str, Any]:
        """Get the health status of all components."""
        return {
            "chromadb_available": self.chroma_connector.is_available(),
            "semantic_search_available": self.semantic_search.is_available(),
            "knowledge_dir": str(self.knowledge_dir),
            "components": {
                "pattern_manager": "healthy",
                "error_solution_manager": "healthy", 
                "pattern_classification": "healthy",
                "tech_detector": "healthy"
            }
        }