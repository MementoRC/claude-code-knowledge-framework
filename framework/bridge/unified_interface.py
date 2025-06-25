#!/usr/bin/env python3
"""
Unified Knowledge Management Interface

Integrates feature flags with knowledge management for controlled capability rollout.
Provides a unified API for knowledge management with feature gating and runtime flag control.
"""

from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

from ..core.knowledge_manager import ClaudeCodeKnowledgeManager
from ..core.feature_flags.flag_configuration_template import (
    FlagConfigurationTemplate,
    AtomicComponent,
    TemplateLevel
)

class UnifiedKnowledgeManager:
    """
    Unified interface combining knowledge management with feature flag control.

    - Integrates with ClaudeCodeKnowledgeManager
    - Uses feature flags for capability control (atomic design)
    - Provides unified API for knowledge management with feature gating
    - Supports dynamic capability detection and runtime flag changes
    - Includes error handling and graceful fallback
    - Maintains backward compatibility
    """

    # Known capabilities that can be controlled by feature flags
    KNOWN_CAPABILITIES = [
        "semantic_search",
        "pattern_extraction",
        "session_analysis",
        "enhanced_indexing",
        "backup_restore",
        "performance_monitoring"
    ]

    def __init__(self, knowledge_dir: str = ".claude/knowledge"):
        self._knowledge_manager = ClaudeCodeKnowledgeManager(knowledge_dir)
        self._feature_template = self._create_feature_template()
        self._logger = logging.getLogger(__name__)
        # Runtime feature flag state (default: use template defaults)
        self._feature_flags: Dict[str, bool] = {
            f"enable_{cap}": comp.config.get("default", True)
            for cap, comp in self._feature_template._components.items()
        }

    def _create_feature_template(self) -> FlagConfigurationTemplate:
        """Create feature flag template for knowledge management capabilities."""
        template = FlagConfigurationTemplate()
        for capability in self.KNOWN_CAPABILITIES:
            template.add_component(AtomicComponent(
                name=f"enable_{capability}",
                level=TemplateLevel.ATOM,
                config={"default": True, "type": "boolean"}
            ))
        return template

    def set_flag(self, flag_name: str, value: bool) -> None:
        """Set a feature flag at runtime."""
        if flag_name in self._feature_flags:
            self._feature_flags[flag_name] = value
            self._logger.info(f"Feature flag '{flag_name}' set to {value}")
        else:
            self._logger.warning(f"Unknown feature flag: {flag_name}")

    def get_flag(self, flag_name: str) -> Optional[bool]:
        """Get the value of a feature flag."""
        return self._feature_flags.get(flag_name)

    def get_capabilities(self) -> Dict[str, bool]:
        """Get current capability status based on feature flags."""
        return {
            cap: self._feature_flags.get(f"enable_{cap}", True)
            for cap in self.KNOWN_CAPABILITIES
        }

    def capture_session_knowledge(self, session_data: Dict[str, Any],
                                 lessons_learned: Optional[List[str]] = None,
                                 solution_patterns: Optional[List[Dict[str, Any]]] = None,
                                 manual_insights: Optional[List[str]] = None) -> str:
        """Capture session knowledge with feature flag checks."""
        try:
            capabilities = self.get_capabilities()
            if not capabilities.get("enhanced_indexing", True):
                self._logger.warning("Enhanced indexing disabled by feature flag")
            # Always call the underlying manager for backward compatibility
            return self._knowledge_manager.capture_session_knowledge(
                session_data,
                lessons_learned or [],
                solution_patterns or [],
                manual_insights
            )
        except Exception as e:
            self._logger.error(f"Failed to capture session knowledge: {e}")
            raise

    def search_knowledge(self, query: str, context: Optional[Dict[str, Any]] = None,
                        max_results: int = 10) -> List[Dict[str, Any]]:
        """Search knowledge with feature-controlled capabilities."""
        try:
            capabilities = self.get_capabilities()
            if not capabilities.get("semantic_search", True):
                self._logger.info("Semantic search disabled by feature flag, using fallback")
                # Optionally, could force keyword search here if supported
            else:
                if hasattr(self._knowledge_manager, "semantic_search"):
                    if self._knowledge_manager.semantic_search.is_available():
                        self._logger.info("Semantic search engine available")
                    else:
                        self._logger.info("Semantic search unavailable, using keyword fallback")
            return self._knowledge_manager.search_knowledge(query, context, max_results)
        except Exception as e:
            self._logger.error(f"Knowledge search failed: {e}")
            # Graceful degradation - return empty results
            return []

    def get_session_context_summary(self, days_back: int = 7) -> Dict[str, Any]:
        """Get session context summary with feature flag control."""
        capabilities = self.get_capabilities()
        if not capabilities.get("pattern_extraction", True):
            self._logger.warning("Pattern extraction disabled by feature flag")
            return {"total_sessions": 0, "success_rate": 0.0}
        try:
            return self._knowledge_manager.get_session_context_summary(days_back)
        except Exception as e:
            self._logger.error(f"Session context summary failed: {e}")
            return {"total_sessions": 0, "success_rate": 0.0}

    def suggest_solutions(self, context: Dict[str, Any], error_pattern: str) -> List[Dict[str, Any]]:
        """Suggest solutions with feature gating."""
        capabilities = self.get_capabilities()
        if not capabilities.get("session_analysis", True):
            self._logger.warning("Solution suggestions disabled by feature flag")
            return []
        try:
            # The underlying manager expects (current_failures, context)
            # For backward compatibility, try both signatures
            try:
                # Newer signature: (current_failures, context)
                return self._knowledge_manager.suggest_solutions([error_pattern], context)
            except TypeError:
                # Fallback: (context, error_pattern)
                return self._knowledge_manager.suggest_solutions(context, error_pattern)
        except Exception as e:
            self._logger.error(f"Solution suggestion failed: {e}")
            return []

    def backup_knowledge_base(self, backup_path: str) -> bool:
        """Backup knowledge base with feature control."""
        capabilities = self.get_capabilities()
        if not capabilities.get("backup_restore", True):
            self._logger.warning("Backup/restore disabled by feature flag")
            return False
        try:
            import shutil
            shutil.copytree(self._knowledge_manager.knowledge_dir, backup_path, dirs_exist_ok=True)
            return True
        except Exception as e:
            self._logger.error(f"Backup failed: {e}")
            return False

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics with feature control."""
        capabilities = self.get_capabilities()
        if not capabilities.get("performance_monitoring", True):
            return {"monitoring": "disabled"}
        try:
            context_summary = self._knowledge_manager.get_session_context_summary(30)
            return {
                "total_sessions": context_summary.get("total_sessions", 0),
                "knowledge_base_size": self._get_knowledge_base_size(),
                "success_rate": context_summary.get("success_rate", 0.0)
            }
        except Exception as e:
            self._logger.error(f"Performance metrics failed: {e}")
            return {"error": str(e)}

    def _get_knowledge_base_size(self) -> int:
        """Get approximate knowledge base size."""
        try:
            knowledge_path = Path(self._knowledge_manager.knowledge_dir)
            total_size = sum(f.stat().st_size for f in knowledge_path.rglob('*') if f.is_file())
            return total_size
        except Exception:
            return 0

    def get_health_status(self) -> Dict[str, Any]:
        """Get unified system health status."""
        capabilities = self.get_capabilities()
        return {
            "knowledge_manager": "healthy",
            "capabilities": capabilities,
            "active_features": sum(1 for v in capabilities.values() if v),
            "total_features": len(capabilities),
            "feature_template": self._feature_template.compose_template(),
            "feature_flags": self._feature_flags.copy()
        }
