"""
FastAPI dependencies for UCKN API.
"""

from fastapi import HTTPException

from ..core.organisms.knowledge_manager import KnowledgeManager

# Global knowledge manager instance
_knowledge_manager: KnowledgeManager = None


def get_knowledge_manager() -> KnowledgeManager:
    """Dependency to get knowledge manager instance."""
    global _knowledge_manager
    if _knowledge_manager is None:
        raise HTTPException(status_code=503, detail="Knowledge manager not initialized")
    return _knowledge_manager


def set_knowledge_manager(km: KnowledgeManager) -> None:
    """Set the global knowledge manager instance."""
    global _knowledge_manager
    _knowledge_manager = km