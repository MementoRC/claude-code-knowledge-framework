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
from ...storage import UnifiedDatabase # Changed from ChromaDBConnector


class KnowledgeManager:
    """Core knowledge management system using a Unified Database for storage."""

    def __init__(self, knowledge_dir: str = ".uckn/knowledge", pg_db_url: str = "postgresql://user:password@localhost:5432/uckn_db"):
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger(__name__)

        # Initialize Unified Database connector
        self.unified_db = UnifiedDatabase(
            pg_db_url=pg_db_url,
            chroma_db_path=str(self.knowledge_dir / "chroma_db")
        )
        if not self.unified_db.is_available():
            self._logger.warning("Unified Database (PostgreSQL and/or ChromaDB) is not fully available. Knowledge storage and retrieval will be limited.")

        # Initialize Semantic Search for embeddings
        self.semantic_search = SemanticSearch(knowledge_dir=str(self.knowledge_dir))
        if not self.semantic_search.is_available():
            self._logger.warning("Semantic search model not available. Embeddings cannot be generated.")

        # Initialize molecules, passing the unified_db
        self.pattern_manager = PatternManager(self.unified_db, self.semantic_search)
        self.error_solution_manager = ErrorSolutionManager(self.unified_db, self.semantic_search)
        self.pattern_classification = PatternClassification(self.unified_db) # PatternClassification now uses UnifiedDB
        
        # Initialize atoms
        self.tech_detector = TechStackDetector()

    # Project management methods (new)
    def add_project(self, name: str, description: Optional[str] = None) -> Optional[str]:
        """Add a new project."""
        return self.unified_db.add_project(name, description)

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific project."""
        return self.unified_db.get_project(project_id)

    def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing project."""
        return self.unified_db.update_project(project_id, updates)

    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        return self.unified_db.delete_project(project_id)

    def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects."""
        return self.unified_db.get_all_projects()

    # Pattern management methods
    def add_pattern(self, pattern_data: Dict[str, Any]) -> Optional[str]:
        """Add a new knowledge pattern."""
        # pattern_data should now include 'document', 'metadata', and optionally 'project_id'
        document_text = pattern_data.get("document")
        metadata = pattern_data.get("metadata", {})
        project_id = pattern_data.get("project_id")

        if not document_text:
            self._logger.error("Pattern data must include 'document' text for embedding.")
            return None
        if not self.semantic_search.is_available():
            self._logger.error("Semantic search not available, cannot generate embeddings for pattern.")
            return None

        embedding = self.semantic_search.encode(document_text)
        if embedding is None:
            self._logger.error("Failed to generate embedding for pattern.")
            return None

        return self.unified_db.add_pattern(
            document_text=document_text,
            embedding=embedding,
            metadata=metadata,
            pattern_id=pattern_data.get("pattern_id"),
            project_id=project_id
        )

    def get_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific pattern."""
        return self.unified_db.get_pattern(pattern_id)

    def update_pattern(self, pattern_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing pattern."""
        document_text = updates.get("document")
        metadata = updates.get("metadata")
        project_id = updates.get("project_id")
        embedding = None

        if document_text and self.semantic_search.is_available():
            embedding = self.semantic_search.encode(document_text)
            if embedding is None:
                self._logger.error(f"Failed to generate new embedding for pattern {pattern_id} during update.")
                return False
        elif document_text:
            self._logger.warning("Semantic search not available, cannot re-generate embedding for updated document text.")

        return self.unified_db.update_pattern(
            pattern_id=pattern_id,
            document_text=document_text,
            embedding=embedding,
            metadata=metadata,
            project_id=project_id
        )

    def delete_pattern(self, pattern_id: str) -> bool:
        """Delete a pattern."""
        return self.unified_db.delete_pattern(pattern_id)

    def search_patterns(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.7,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for knowledge patterns using semantic similarity."""
        if not self.semantic_search.is_available():
            self._logger.warning("Semantic search not available, cannot generate query embedding.")
            return []
        query_embedding = self.semantic_search.encode(query)
        if query_embedding is None:
            self._logger.error("Failed to generate query embedding for pattern search.")
            return []
        return self.unified_db.search_patterns(query_embedding, limit, min_similarity, metadata_filter)

    # Pattern classification methods
    def create_category(self, name: str, description: str = "", category_id: Optional[str] = None) -> Optional[str]:
        """Create a new pattern category."""
        return self.unified_db.add_category(name, description, category_id)

    def get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific category."""
        return self.unified_db.get_category(category_id)

    def update_category(self, category_id: str, name: Optional[str] = None, description: Optional[str] = None) -> bool:
        """Update an existing category."""
        updates = {}
        if name is not None: updates["name"] = name
        if description is not None: updates["description"] = description
        if not updates: return False # No updates provided
        return self.unified_db.update_category(category_id, updates)

    def delete_category(self, category_id: str) -> bool:
        """Delete a category."""
        return self.unified_db.delete_category(category_id)

    def assign_pattern_to_category(self, pattern_id: str, category_id: str) -> bool:
        """Assign a pattern to a category."""
        return self.unified_db.assign_pattern_to_category(pattern_id, category_id)

    def remove_pattern_from_category(self, pattern_id: str, category_id: str) -> bool:
        """Remove a pattern from a category."""
        return self.unified_db.remove_pattern_from_category(pattern_id, category_id)

    def get_patterns_by_category(self, category_id: str) -> List[str]:
        """Get all pattern IDs in a category."""
        return self.unified_db.get_patterns_by_category(category_id)

    def get_pattern_categories(self, pattern_id: str) -> List[Dict[str, Any]]:
        """Get all categories assigned to a pattern."""
        return self.unified_db.get_pattern_categories(pattern_id)

    # Error solution management methods
    def add_error_solution(self, solution_data: Dict[str, Any]) -> Optional[str]:
        """Add a new error solution."""
        document_text = solution_data.get("document")
        metadata = solution_data.get("metadata", {})
        project_id = solution_data.get("project_id")

        if not document_text:
            self._logger.error("Solution data must include 'document' text for embedding.")
            return None
        if not self.semantic_search.is_available():
            self._logger.error("Semantic search not available, cannot generate embeddings for error solution.")
            return None

        embedding = self.semantic_search.encode(document_text)
        if embedding is None:
            self._logger.error("Failed to generate embedding for error solution.")
            return None

        return self.unified_db.add_error_solution(
            document_text=document_text,
            embedding=embedding,
            metadata=metadata,
            solution_id=solution_data.get("solution_id"),
            project_id=project_id
        )

    def get_error_solution(self, solution_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific error solution."""
        return self.unified_db.get_error_solution(solution_id)

    def search_error_solutions(
        self,
        error_query: str,
        limit: int = 10,
        min_similarity: float = 0.7,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for error solutions using semantic similarity."""
        if not self.semantic_search.is_available():
            self._logger.warning("Semantic search not available, cannot generate query embedding.")
            return []
        query_embedding = self.semantic_search.encode(error_query)
        if query_embedding is None:
            self._logger.error("Failed to generate query embedding for error search.")
            return []
        return self.unified_db.search_error_solutions(query_embedding, limit, min_similarity, metadata_filter)

    # Team Access Management (new)
    def add_team_access(self, user_id: str, project_id: str, role: str) -> Optional[str]:
        """Add team access for a user to a project."""
        return self.unified_db.add_team_access(user_id, project_id, role)

    def get_team_access(self, access_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve specific team access."""
        return self.unified_db.get_team_access(access_id)

    def update_team_access(self, access_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing team access."""
        return self.unified_db.update_team_access(access_id, updates)

    def delete_team_access(self, access_id: str) -> bool:
        """Delete team access."""
        return self.unified_db.delete_team_access(access_id)

    def get_team_access_for_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all team access records for a project."""
        return self.unified_db.get_team_access_for_project(project_id)

    # Compatibility Matrix Management (new)
    def add_compatibility_entry(
        self, source_tech: str, target_tech: str, compatibility_score: float, notes: Optional[str] = None
    ) -> Optional[str]:
        """Add a new compatibility matrix entry."""
        return self.unified_db.add_compatibility_entry(source_tech, target_tech, compatibility_score, notes)

    def get_compatibility_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific compatibility matrix entry."""
        return self.unified_db.get_compatibility_entry(entry_id)

    def update_compatibility_entry(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing compatibility matrix entry."""
        return self.unified_db.update_compatibility_entry(entry_id, updates)

    def delete_compatibility_entry(self, entry_id: str) -> bool:
        """Delete a compatibility matrix entry."""
        return self.unified_db.delete_compatibility_entry(entry_id)

    def search_compatibility_entries(
        self,
        source_tech: Optional[str] = None,
        target_tech: Optional[str] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search compatibility entries."""
        return self.unified_db.search_compatibility_entries(source_tech, target_tech, min_score, max_score)

    # Tech stack analysis
    def analyze_project_stack(self, project_path: str) -> Dict[str, Any]:
        """Analyze project technology stack."""
        return self.tech_detector.analyze_project(project_path)

    def get_all_patterns_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all patterns filtered by status. Used by workflow manager."""
        try:
            # Use the unified database to search patterns by status
            return self.unified_db.search_patterns_by_metadata({"status": status})
        except Exception as e:
            self._logger.error(f"Error searching patterns by status {status}: {e}")
            return []

    # Health and utility methods
    def get_health_status(self) -> Dict[str, Any]:
        """Get the health status of all components."""
        unified_db_status = self.unified_db.is_available()
        return {
            "unified_db_available": unified_db_status,
            "semantic_search_available": self.semantic_search.is_available(),
            "knowledge_dir": str(self.knowledge_dir),
            "components": {
                "pattern_manager": "healthy" if unified_db_status and self.semantic_search.is_available() else "degraded",
                "error_solution_manager": "healthy" if unified_db_status and self.semantic_search.is_available() else "degraded",
                "pattern_classification": "healthy" if unified_db_status else "degraded",
                "tech_detector": "healthy"
            }
        }
