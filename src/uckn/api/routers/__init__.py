"""
UCKN API Routers
Contains all FastAPI router modules for different API endpoints.
"""

# Import routers to make them available for main.py
from . import patterns, projects, collaboration, health

__all__ = ["patterns", "projects", "collaboration", "health"]
