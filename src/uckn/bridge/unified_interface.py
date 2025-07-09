#!/usr/bin/env python3
"""
Unified Knowledge Management Interface

Integrates feature flags with knowledge management for controlled capability rollout.
Provides a unified API for knowledge management with feature gating and runtime flag control.
"""

import logging
from pathlib import Path
from typing import Any, Optional

# Updated to use current UCKN atomic framework
from ..core.organisms.knowledge_manager import KnowledgeManager
from ..feature_flags.flag_configuration_template import (
    AtomicComponent,
    FlagConfigurationTemplate,
    TemplateLevel,
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
        "performance_monitoring",
    ]

    def __init__(self, knowledge_dir: str = ".uckn/knowledge"):
        self._knowledge_manager = KnowledgeManager(knowledge_dir)
        self._feature_template = self._create_feature_template()
        self._logger = logging.getLogger(__name__)
        # Runtime feature flag state (default: use template defaults)
        self._feature_flags: dict[str, bool] = {
            f"enable_{cap}": comp.config.get("default", True)
            for cap, comp in self._feature_template._components.items()
        }

    def _create_feature_template(self) -> FlagConfigurationTemplate:
        """Create feature flag template for knowledge management capabilities."""
        template = FlagConfigurationTemplate()
        for capability in self.KNOWN_CAPABILITIES:
            template.add_component(
                AtomicComponent(
                    name=f"enable_{capability}",
                    level=TemplateLevel.ATOM,
                    config={"default": True, "type": "boolean"},
                )
            )
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

    def get_capabilities(self) -> dict[str, bool]:
        """Get current capability status based on feature flags."""
        return {
            cap: self._feature_flags.get(f"enable_{cap}", True)
            for cap in self.KNOWN_CAPABILITIES
        }

    def add_knowledge_pattern(self, pattern_data: dict[str, Any]) -> Optional[str]:
        """Add a knowledge pattern with feature flag checks."""
        try:
            capabilities = self.get_capabilities()
            if not capabilities.get("enhanced_indexing", True):
                self._logger.warning("Enhanced indexing disabled by feature flag")
                return None
            return self._knowledge_manager.add_pattern(pattern_data)
        except Exception as e:
            self._logger.error(f"Failed to add knowledge pattern: {e}")
            return None

    def search_patterns(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.7,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search knowledge patterns with feature-controlled capabilities."""
        try:
            capabilities = self.get_capabilities()
            if not capabilities.get("semantic_search", True):
                self._logger.info("Semantic search disabled by feature flag")
                return []
            return self._knowledge_manager.search_patterns(
                query, limit, min_similarity, metadata_filter
            )
        except Exception as e:
            self._logger.error(f"Pattern search failed: {e}")
            return []

    def get_pattern(self, pattern_id: str) -> dict[str, Any] | None:
        """Get a specific pattern with feature flag control."""
        capabilities = self.get_capabilities()
        if not capabilities.get("pattern_extraction", True):
            self._logger.warning("Pattern extraction disabled by feature flag")
            return None
        try:
            return self._knowledge_manager.get_pattern(pattern_id)
        except Exception as e:
            self._logger.error(f"Pattern retrieval failed: {e}")
            return None

    def search_error_solutions(
        self, error_query: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Search for error solutions with feature gating."""
        capabilities = self.get_capabilities()
        if not capabilities.get("session_analysis", True):
            self._logger.warning("Solution suggestions disabled by feature flag")
            return []
        try:
            return self._knowledge_manager.search_error_solutions(error_query, limit)
        except Exception as e:
            self._logger.error(f"Error solution search failed: {e}")
            return []

    def backup_knowledge_base(self, backup_path: str) -> bool:
        """Backup knowledge base with feature control."""
        capabilities = self.get_capabilities()
        if not capabilities.get("backup_restore", True):
            self._logger.warning("Backup/restore disabled by feature flag")
            return False
        try:
            import shutil

            shutil.copytree(
                self._knowledge_manager.knowledge_dir, backup_path, dirs_exist_ok=True
            )
            return True
        except Exception as e:
            self._logger.error(f"Backup failed: {e}")
            return False

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics with feature control."""
        capabilities = self.get_capabilities()
        if not capabilities.get("performance_monitoring", True):
            return {"monitoring": "disabled"}
        try:
            return {
                "knowledge_base_size": self._get_knowledge_base_size(),
                "chromadb_available": self._knowledge_manager.chroma_connector.is_available(),
                "semantic_search_available": self._knowledge_manager.semantic_search.is_available(),
            }
        except Exception as e:
            self._logger.error(f"Performance metrics failed: {e}")
            return {"error": str(e)}

    def _get_knowledge_base_size(self) -> int:
        """Get approximate knowledge base size."""
        try:
            knowledge_path = Path(self._knowledge_manager.knowledge_dir)
            total_size = sum(
                f.stat().st_size for f in knowledge_path.rglob("*") if f.is_file()
            )
            return total_size
        except Exception:
            return 0

    def get_health_status(self) -> dict[str, Any]:
        """Get unified system health status."""
        capabilities = self.get_capabilities()
        return {
            "knowledge_manager": "healthy",
            "capabilities": capabilities,
            "active_features": sum(1 for v in capabilities.values() if v),
            "total_features": len(capabilities),
            "feature_template": self._feature_template.compose_template(),
            "feature_flags": self._feature_flags.copy(),
        }
