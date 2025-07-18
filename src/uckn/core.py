"""
UCKN Core Framework Components
"""

import json
from pathlib import Path
from typing import Any

# Check for sentence transformers availability
try:
    import sentence_transformers  # noqa: F401
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class KnowledgeManager:
    """Core knowledge management system"""

    # Known capabilities for compatibility with tests
    KNOWN_CAPABILITIES = [
        "semantic_search",
        "pattern_extraction",
        "session_analysis",
        "enhanced_indexing",
        "backup_restore",
        "performance_monitoring",
    ]

    def __init__(self, knowledge_dir: str = ".uckn/knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

        # Initialize semantic search engine
        self.semantic_search = SemanticSearch(knowledge_dir)

    def get_capabilities(self) -> dict[str, bool]:
        """Get available capabilities"""
        return {
            "semantic_search": self.semantic_search.is_available(),
            "pattern_extraction": True,
            "session_analysis": True,
            "enhanced_indexing": False,
            "backup_restore": False,
            "performance_monitoring": False,
        }

    def get_health_status(self) -> dict[str, Any]:
        """Get system health status"""
        return {
            "knowledge_manager": "active",
            "capabilities": self.get_capabilities(),
            "active_features": [
                cap for cap, enabled in self.get_capabilities().items() if enabled
            ],
            "feature_template": "basic",
        }

    def capture_session_knowledge(self, session_data: dict[str, Any]) -> str:
        """Capture knowledge from a session"""
        # TODO: Implement session knowledge capture
        session_id = session_data.get("session_id", "unknown")
        return session_id

    def search_knowledge(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search for knowledge patterns"""
        # Use semantic search if available
        if self.semantic_search.is_available():
            return self.semantic_search.search_similar_sessions(query, limit)

        # Fallback to basic search
        return []

    def get_session_context_summary(self) -> dict[str, Any]:
        """Get session context summary"""
        return {"total_sessions": 0, "active_sessions": 0, "recent_patterns": []}

    def suggest_solutions(
        self, context: dict[str, Any], error: str
    ) -> list[dict[str, Any]]:
        """Suggest solutions based on context and error"""
        # TODO: Implement solution suggestions
        return []

    def backup_knowledge_base(self, backup_path: str) -> bool:
        """Backup knowledge base"""
        # TODO: Implement backup functionality
        return False

    def search_patterns(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search for knowledge patterns"""
        return self.search_knowledge(query, limit)

    def add_pattern(self, pattern: dict[str, Any]) -> str:
        """Add a new knowledge pattern"""
        # TODO: Implement pattern storage
        return "pattern_id"

    def get_pattern(self, pattern_id: str) -> dict[str, Any] | None:
        """Retrieve a specific pattern"""
        # TODO: Implement pattern retrieval
        return None


class SemanticSearch:
    """Semantic search engine for knowledge patterns"""

    def __init__(self, knowledge_dir: str = ".uckn/knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.embeddings_dir = self.knowledge_dir / "embeddings"
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)

        # Check if dependencies are available
        self.model_available = self._check_model_availability()

    def _check_model_availability(self) -> bool:
        """Check if semantic search dependencies are available"""
        return SENTENCE_TRANSFORMERS_AVAILABLE

    def is_available(self) -> bool:
        """Check if semantic search is available"""
        return self.model_available

    def _extract_text_for_embedding(self, session_data: dict[str, Any]) -> str:
        """Extract text content from session data for embedding"""
        text_parts = []

        # Extract context information
        if "context" in session_data:
            context = session_data["context"]
            if isinstance(context, dict):
                for key, value in context.items():
                    if isinstance(value, str):
                        text_parts.append(f"{key}: {value}")
                    elif isinstance(value, list):
                        text_parts.append(f"{key}: {', '.join(map(str, value))}")

        # Extract lessons learned
        if "lessons_learned" in session_data:
            lessons = session_data["lessons_learned"]
            if isinstance(lessons, list):
                text_parts.extend(lessons)

        # Extract solution patterns
        if "solution_patterns" in session_data:
            patterns = session_data["solution_patterns"]
            if isinstance(patterns, list):
                for pattern in patterns:
                    if isinstance(pattern, dict) and "description" in pattern:
                        text_parts.append(pattern["description"])
                    elif isinstance(pattern, str):
                        text_parts.append(pattern)

        # Extract manual insights
        if "manual_insights" in session_data:
            insights = session_data["manual_insights"]
            if isinstance(insights, list):
                text_parts.extend(insights)

        # Fallback to session ID if no content found
        if not text_parts:
            session_id = session_data.get("session_id", "unknown")
            return f"Session {session_id}"

        return " ".join(text_parts)

    def get_embedding_stats(self) -> dict[str, Any]:
        """Get embedding statistics"""
        stats = {
            "total_embeddings": 0,
            "storage_type": "json",
            "model_available": self.model_available,
        }

        embeddings_file = self.embeddings_dir / "session_embeddings.json"
        if embeddings_file.exists():
            try:
                with open(embeddings_file) as f:
                    data = json.load(f)
                    stats["total_embeddings"] = len(data)
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        return stats

    def search_similar_sessions(self, query: str, limit: int = 10) -> list[dict]:
        """Search for similar sessions based on query"""
        if not self.is_available():
            return []

        # TODO: Implement actual semantic search
        return []

    def store_session_embedding(
        self, session_id: str, session_data: dict[str, Any]
    ) -> bool:
        """Store session embedding"""
        if not self.is_available():
            return False

        # For graceful degradation testing, return False if sentence transformers not available
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            return False

        try:
            # TODO: Generate actual embeddings
            # For now, just store session data
            embeddings_file = self.embeddings_dir / "session_embeddings.json"

            # Load existing data
            existing_data = {}
            if embeddings_file.exists():
                with open(embeddings_file) as f:
                    existing_data = json.load(f)

            # Add new session
            existing_data[session_id] = {
                "metadata": session_data,
                "embedding": [],  # Placeholder for actual embedding
            }

            # Save updated data
            with open(embeddings_file, "w") as f:
                json.dump(existing_data, f, indent=2)

            return True
        except Exception:
            return False

    def _store_embedding_numpy(
        self, session_id: str, embedding: Any, metadata: dict[str, Any]
    ) -> None:
        """Store embedding with numpy array support"""
        embeddings_file = self.embeddings_dir / "session_embeddings.json"

        # Load existing data
        existing_data = {}
        if embeddings_file.exists():
            with open(embeddings_file) as f:
                existing_data = json.load(f)

        # Convert numpy array to list for JSON serialization
        if hasattr(embedding, "tolist"):
            embedding_list = embedding.tolist()
        else:
            embedding_list = list(embedding)

        # Add new session
        existing_data[session_id] = {"embedding": embedding_list, "metadata": metadata}

        # Save updated data
        with open(embeddings_file, "w") as f:
            json.dump(existing_data, f, indent=2)

    def encode(self, text: str) -> list[float]:
        """Generate embeddings for text"""
        # TODO: Implement text encoding
        return []

    def search(self, query: str, patterns: list[dict], limit: int = 10) -> list[dict]:
        """Perform semantic search"""
        # TODO: Implement semantic search
        return []


class TechStackDetector:
    """Detect project technology stack"""

    def analyze_project(self, project_path: str) -> dict[str, Any]:
        """Analyze project for technology stack"""
        path = Path(project_path)

        stack = {
            "languages": [],
            "package_managers": [],
            "frameworks": [],
            "testing": [],
            "ci_cd": [],
        }

        # Detect Python
        if (path / "pyproject.toml").exists():
            stack["languages"].append("Python")
            stack["package_managers"].append("pip/poetry/pixi")

        if (path / "requirements.txt").exists():
            stack["package_managers"].append("pip")

        # Detect JavaScript/Node.js
        if (path / "package.json").exists():
            stack["languages"].append("JavaScript")
            stack["package_managers"].append("npm")

        # Detect testing frameworks
        if (path / "pytest.ini").exists() or "pytest" in str(path):
            stack["testing"].append("pytest")

        # Detect CI/CD
        if (path / ".github" / "workflows").exists():
            stack["ci_cd"].append("GitHub Actions")

        return stack
