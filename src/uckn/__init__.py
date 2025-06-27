"""
Universal Claude Code Knowledge Network (UCKN)
AI-powered development knowledge management framework
"""

__version__ = "1.0.0"
__author__ = "Claude Code Community"
__email__ = "noreply@anthropic.com"

from .core.organisms.knowledge_manager import KnowledgeManager
from .core.atoms.semantic_search import SemanticSearch
from .bridge.unified_interface import UnifiedKnowledgeManager
from .cli import main as cli_main

__all__ = [
    "KnowledgeManager",
    "SemanticSearch",
    "UnifiedKnowledgeManager", 
    "cli_main",
    "__version__",
]