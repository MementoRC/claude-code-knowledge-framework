"""
UCKN Core Molecules
Composite components combining multiple atoms for specific functionalities
"""

from .pattern_manager import PatternManager
from .error_solution_manager import ErrorSolutionManager
from .pattern_migrator import PatternMigrator

__all__ = [
    "PatternManager",
    "ErrorSolutionManager", 
    "PatternMigrator"
]