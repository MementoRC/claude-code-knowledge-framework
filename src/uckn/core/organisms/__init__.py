"""
UCKN Core Organisms
Complex components that orchestrate multiple molecules and atoms
"""

from .knowledge_manager import KnowledgeManager
from .pattern_recommendation_engine import PatternRecommendationEngine

__all__ = [
    "KnowledgeManager",
    "PatternRecommendationEngine"
]