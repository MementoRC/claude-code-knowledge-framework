#!/usr/bin/env python3
"""
Bridge Interface Module

Unified interface layer that integrates feature flags with knowledge management.
Provides a unified API for knowledge management with feature gating.
"""

from .unified_interface import UnifiedKnowledgeManager

__all__ = ["UnifiedKnowledgeManager"]
