"""UCKN Core Module - Main components for knowledge management."""

from .atoms.semantic_search import SEMANTIC_SEARCH_ENGINE_AVAILABLE, SemanticSearch
from .organisms.knowledge_manager import KnowledgeManager

# Expose for backward compatibility with tests
SENTENCE_TRANSFORMERS_AVAILABLE = SEMANTIC_SEARCH_ENGINE_AVAILABLE

__all__ = ["KnowledgeManager", "SemanticSearch", "SENTENCE_TRANSFORMERS_AVAILABLE"]
