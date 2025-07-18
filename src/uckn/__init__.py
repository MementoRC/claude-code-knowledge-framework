"""
Universal Claude Code Knowledge Network (UCKN)
AI-powered development knowledge management framework
"""

__version__ = "1.0.0"
__author__ = "Claude Code Community"
__email__ = "noreply@anthropic.com"

from .cli import main as cli_main
from .core import KnowledgeManager, SemanticSearch

__all__ = [
    "KnowledgeManager",
    "SemanticSearch",
    "cli_main",
    "__version__",
]
