"""
FastAPI dependencies for UCKN API.
"""

from fastapi import HTTPException

from ..core.organisms.knowledge_manager import KnowledgeManager
from ..core.organisms.predictive_issue_detector import PredictiveIssueDetector
from ..core.atoms.tech_stack_detector import TechStackDetector
from ..core.molecules.issue_detection_rules import IssueDetectionRules
from ..core.molecules.issue_prediction_models import IssuePredictionModels

# Global instances
_knowledge_manager: KnowledgeManager = None
_predictive_issue_detector: PredictiveIssueDetector = None


def get_knowledge_manager() -> KnowledgeManager:
    """Dependency to get knowledge manager instance."""
    global _knowledge_manager
    if _knowledge_manager is None:
        raise HTTPException(status_code=503, detail="Knowledge manager not initialized")
    return _knowledge_manager


def set_knowledge_manager(km: KnowledgeManager) -> None:
    """Set the global knowledge manager instance."""
    global _knowledge_manager
    _knowledge_manager = km


def get_predictive_issue_detector() -> PredictiveIssueDetector:
    """Dependency to get predictive issue detector instance."""
    global _predictive_issue_detector
    if _predictive_issue_detector is None:
        # Initialize the predictive issue detector with required components
        try:
            # Get knowledge manager
            km = get_knowledge_manager()
            
            # Initialize components
            tech_stack_detector = TechStackDetector()
            issue_detection_rules = IssueDetectionRules(tech_stack_detector)
            issue_prediction_models = IssuePredictionModels()
            
            # Create the detector
            _predictive_issue_detector = PredictiveIssueDetector(
                tech_stack_detector=tech_stack_detector,
                issue_detection_rules=issue_detection_rules,
                issue_prediction_models=issue_prediction_models,
                error_solution_manager=km.error_solution_manager,
                pattern_analytics=km.pattern_analytics
            )
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Predictive issue detector not available: {e}")
    
    return _predictive_issue_detector


def set_predictive_issue_detector(detector: PredictiveIssueDetector) -> None:
    """Set the global predictive issue detector instance."""
    global _predictive_issue_detector
    _predictive_issue_detector = detector