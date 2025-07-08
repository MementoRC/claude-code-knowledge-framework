"""
UCKN Predictions Router

Provides REST API endpoints for predictive issue detection.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ...core.organisms.predictive_issue_detector import PredictiveIssueDetector
from ..dependencies import get_predictive_issue_detector

router = APIRouter()
_logger = logging.getLogger(__name__)

# --- Request and Response Models ---


class PredictionRequest(BaseModel):
    """Request model for issue prediction."""

    project_path: str = Field(..., description="File system path to the project root.")
    code_snippet: Optional[str] = Field(
        None, description="Optional code snippet for analysis."
    )
    context_description: Optional[str] = Field(
        None, description="Optional natural language description of the context."
    )
    project_id: Optional[str] = Field(
        None, description="Optional ID of the project in UCKN."
    )


class PredictedIssue(BaseModel):
    """Model for a single predicted issue."""

    type: str = Field(
        ...,
        description="Type of the predicted issue (e.g., 'dependency_conflict', 'ml_performance_issue').",
    )
    description: str = Field(
        ..., description="Detailed description of the potential issue."
    )
    severity: str = Field(
        ..., description="Severity of the issue (e.g., 'low', 'medium', 'high')."
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0) of the prediction.",
    )
    preventive_measure: str = Field(
        ..., description="Suggested preventive measure or recommendation."
    )


class PredictionResponse(BaseModel):
    """Response model for issue prediction."""

    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp of the prediction.",
    )
    issues: list[PredictedIssue] = Field(
        ..., description="List of detected potential issues."
    )
    message: str = Field(
        "Prediction completed successfully.", description="Status message."
    )


class FeedbackRequest(BaseModel):
    """Request model for providing feedback on a predicted issue."""

    issue_id: str = Field(
        ..., description="Unique identifier for the detected issue instance."
    )
    project_id: Optional[str] = Field(
        None, description="Optional ID of the project this feedback relates to."
    )
    outcome: str = Field(
        ...,
        description="Actual outcome of the issue (e.g., 'resolved', 'false_positive', 'ignored', 'still_active').",
    )
    resolution_details: Optional[str] = Field(
        None, description="Optional details about how the issue was resolved."
    )
    time_to_resolve_minutes: Optional[float] = Field(
        None, description="Optional time taken to resolve the issue."
    )
    feedback_data: Optional[dict[str, Any]] = Field(
        None, description="Additional arbitrary feedback data."
    )


class FeedbackResponse(BaseModel):
    """Response model for feedback submission."""

    success: bool = Field(
        ..., description="True if feedback was recorded successfully."
    )
    message: str = Field(..., description="Status message.")


# --- API Endpoints ---


@router.post(
    "/predictions/detect",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
)
async def detect_issues_endpoint(
    request: PredictionRequest,
    detector: PredictiveIssueDetector = Depends(get_predictive_issue_detector),
):
    """
    Endpoint to detect potential issues in a given project context.
    This can be integrated into CI/CD pipelines or IDEs for early warnings.
    """
    _logger.info(
        f"Received prediction request for project_path: {request.project_path}"
    )
    try:
        detected_issues = detector.detect_issues(
            project_path=request.project_path,
            code_snippet=request.code_snippet,
            context_description=request.context_description,
            project_id=request.project_id,
        )
        # Convert detected issues (Dict[str, Any]) to PredictedIssue Pydantic models
        predicted_issues_models = [PredictedIssue(**issue) for issue in detected_issues]
        return PredictionResponse(issues=predicted_issues_models)
    except Exception as e:
        _logger.exception(f"Error during issue detection for {request.project_path}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect issues: {e}",
        )


@router.post(
    "/predictions/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_200_OK,
)
async def submit_feedback_endpoint(
    request: FeedbackRequest,
    detector: PredictiveIssueDetector = Depends(get_predictive_issue_detector),
):
    """
    Endpoint to submit feedback on a previously detected issue.
    This feedback is crucial for improving the accuracy of the predictive models.
    """
    _logger.info(
        f"Received feedback for issue_id: {request.issue_id}, outcome: {request.outcome}"
    )
    try:
        success = detector.provide_feedback(
            issue_id=request.issue_id,
            project_id=request.project_id,
            outcome=request.outcome,
            resolution_details=request.resolution_details,
            time_to_resolve_minutes=request.time_to_resolve_minutes,
            feedback_data=request.feedback_data,
        )
        if success:
            return FeedbackResponse(
                success=True, message="Feedback recorded successfully."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to record feedback.",
            )
    except Exception as e:
        _logger.exception(f"Error submitting feedback for {request.issue_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {e}",
        )
