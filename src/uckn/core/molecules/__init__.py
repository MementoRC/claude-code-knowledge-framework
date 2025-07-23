"""
UCKN Core Molecules
Composite components combining multiple atoms for specific functionalities
"""

from .error_solution_manager import ErrorSolutionManager
from .pattern_analytics import PatternAnalytics
from .pattern_classification import PatternClassification
from .pattern_manager import PatternManager
from .pattern_migrator import PatternMigrator
from .tech_stack_compatibility_matrix import TechStackCompatibilityMatrix

__all__ = [
    "PatternManager",
    "ErrorSolutionManager",
    "PatternMigrator",
    "PatternAnalytics",
    "TechStackCompatibilityMatrix",
    "PatternClassification"
]
