"""
UCKN Core Molecules
Composite components combining multiple atoms for specific functionalities
"""

from .pattern_manager import PatternManager
from .error_solution_manager import ErrorSolutionManager
from .pattern_migrator import PatternMigrator
from .pattern_analytics import PatternAnalytics

__all__ = [
    "PatternManager",
    "ErrorSolutionManager", 
    "PatternMigrator",
    "PatternAnalytics"
]