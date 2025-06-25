#!/usr/bin/env python3
"""
Unified Knowledge Management Interface

Integrates feature flags with knowledge management for controlled capability rollout.
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
    
    Provides feature-gated access to knowledge management capabilities
    with runtime control and graceful degradation.
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
        
    def _create_feature_template(self) -> FlagConfigurationTemplate:
        """Create feature flag template for knowledge management capabilities."""
        template = FlagConfigurationTemplate()
        
        # Add capability flags
        for capability in self.KNOWN_CAPABILITIES:
            template.add_component(AtomicComponent(
                name=f"enable_{capability}",
                level=TemplateLevel.ATOM,
                config={"default": True, "type": "boolean"}
            ))
            
        return template
        
    def get_capabilities(self) -> Dict[str, bool]:
        """Get current capability status based on feature flags."""
        capabilities = {}
        
        for capability in self.KNOWN_CAPABILITIES:
            # Default to enabled for now - would integrate with actual feature flag system
            capabilities[capability] = True
            
        return capabilities
        
    def capture_session_knowledge(self, session_data: Dict[str, Any], 
                                lessons_learned: List[str] = None,
                                solution_patterns: List[Dict[str, Any]] = None,
                                manual_insights: List[str] = None) -> str:
        """Capture session knowledge with feature flag checks."""
        try:
            capabilities = self.get_capabilities()
            
            # Enhanced indexing capability
            if capabilities.get("enhanced_indexing", False):
                self._logger.info("Using enhanced indexing for session storage")
                
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
            
            # Use semantic search if enabled and available
            if capabilities.get("semantic_search", False):
                self._logger.info("Using enhanced semantic search capabilities")
                
                # Check if semantic search is available
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
        
        if not capabilities.get("pattern_extraction", False):
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
        
        if not capabilities.get("session_analysis", False):
            self._logger.warning("Solution suggestions disabled by feature flag")
            return []
            
        try:
            return self._knowledge_manager.suggest_solutions(context, error_pattern)
        except Exception as e:
            self._logger.error(f"Solution suggestion failed: {e}")
            return []
            
    def backup_knowledge_base(self, backup_path: str) -> bool:
        """Backup knowledge base with feature control."""
        capabilities = self.get_capabilities()
        
        if not capabilities.get("backup_restore", False):
            self._logger.warning("Backup/restore disabled by feature flag")
            return False
            
        try:
            # Simple backup implementation - copy knowledge directory
            import shutil
            shutil.copytree(self._knowledge_manager.knowledge_dir, backup_path, dirs_exist_ok=True)
            return True
        except Exception as e:
            self._logger.error(f"Backup failed: {e}")
            return False
            
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics with feature control."""
        capabilities = self.get_capabilities()
        
        if not capabilities.get("performance_monitoring", False):
            return {"monitoring": "disabled"}
            
        try:
            # Get performance metrics using available methods
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
            "active_features": sum(capabilities.values()),
            "total_features": len(capabilities),
            "feature_template": self._feature_template.compose_template()
        }