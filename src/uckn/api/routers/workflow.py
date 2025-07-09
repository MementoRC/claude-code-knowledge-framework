import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from ...core.molecules.workflow_manager import WorkflowManager
from ...core.organisms.knowledge_manager import KnowledgeManager
from ..dependencies import (
    get_knowledge_manager,
)
from ..models.patterns import PatternStatus  # For consistency

# Import the global ConnectionManager instance directly
from ..models.workflow import (
    InitiateReviewRequest,
    SubmitReviewFeedbackRequest,
    WorkflowActionResponse,
    WorkflowStatusResponse,
    WorkflowTransitionRequest,
)

# Assuming get_knowledge_manager exists
from ..routers.collaboration import (
    manager as connection_manager_instance,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Dependency to get WorkflowManager
def get_workflow_manager(
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager),
) -> WorkflowManager:
    # Pass the global connection_manager_instance directly to WorkflowManager
    return WorkflowManager(knowledge_manager, connection_manager_instance)


# Placeholder for user authentication/authorization
# In a real application, these would come from an authentication system (e.g., OAuth2, JWT)
def get_current_user_id() -> str:
    """Returns a dummy user ID for testing purposes."""
    return "test_user_id"


def get_current_user_roles() -> list[str]:
    """Returns dummy user roles for testing purposes."""
    return ["contributor", "admin"]


@router.post(
    "/patterns/{pattern_id}/workflow/initiate_review",
    response_model=WorkflowActionResponse,
    summary="Initiate review for a pattern",
)
async def initiate_pattern_review(
    pattern_id: str,
    request: InitiateReviewRequest,
    workflow_manager: WorkflowManager = Depends(get_workflow_manager),
    user_id: str = Depends(get_current_user_id),
):
    """
    Submits a pattern from DRAFT state for peer review.
    Assigns reviewers and transitions the pattern to 'in_review' state.
    """
    try:
        response = await workflow_manager.initiate_review(pattern_id, request, user_id)
        return WorkflowActionResponse(**response)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error initiating review for pattern {pattern_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate review: {str(e)}",
        )


@router.post(
    "/patterns/{pattern_id}/workflow/submit_feedback",
    response_model=WorkflowActionResponse,
    summary="Submit review feedback for a pattern",
)
async def submit_pattern_review_feedback(
    pattern_id: str,
    request: SubmitReviewFeedbackRequest,
    workflow_manager: WorkflowManager = Depends(get_workflow_manager),
    user_id: str = Depends(
        get_current_user_id
    ),  # Ensure reviewer_id matches user_id or user has permission
):
    """
    Allows a reviewer to submit feedback for a pattern that is in 'in_review' or 'in_testing' state.
    """
    # Basic authorization check: reviewer_id must match current user or user must be an admin
    if request.reviewer_id != user_id and "admin" not in get_current_user_roles():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not authorized to submit feedback for this reviewer ID.",
        )
    try:
        response = await workflow_manager.submit_review_feedback(pattern_id, request)
        return WorkflowActionResponse(**response)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error submitting feedback for pattern {pattern_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}",
        )


@router.post(
    "/patterns/{pattern_id}/workflow/transition",
    response_model=WorkflowActionResponse,
    summary="Transition a pattern's workflow state",
)
async def transition_pattern_state(
    pattern_id: str,
    request: WorkflowTransitionRequest,
    workflow_manager: WorkflowManager = Depends(get_workflow_manager),
    user_id: str = Depends(get_current_user_id),
    user_roles: list[str] = Depends(get_current_user_roles),
):
    """
    Transitions a pattern to a new workflow state (e.g., approve, reject, publish).
    Requires appropriate user roles (e.g., 'admin' for most transitions).
    """
    # Basic role check: only admins can perform most transitions.
    # Authors can resubmit from REJECTED or DRAFT.
    if "admin" not in user_roles and request.target_state not in [
        PatternStatus.DRAFT,
        PatternStatus.REJECTED,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for this transition.",
        )

    # Ensure the user_id in the request is the authenticated user
    request.user_id = user_id
    try:
        response = await workflow_manager.transition_state(pattern_id, request)
        return WorkflowActionResponse(**response)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error transitioning state for pattern {pattern_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to transition state: {str(e)}",
        )


@router.get(
    "/patterns/{pattern_id}/workflow/status",
    response_model=WorkflowStatusResponse,
    summary="Get a pattern's workflow status",
)
async def get_pattern_workflow_status(
    pattern_id: str, workflow_manager: WorkflowManager = Depends(get_workflow_manager)
):
    """
    Retrieves the current workflow status, review history, and version history for a pattern.
    """
    try:
        status_data = await workflow_manager.get_workflow_status(pattern_id)
        return WorkflowStatusResponse(**status_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error getting workflow status for pattern {pattern_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve workflow status: {str(e)}",
        )


@router.get(
    "/patterns/workflow/pending_reviews",
    response_model=list[
        dict[str, Any]
    ],  # Using Dict[str, Any] for simplicity, could define a specific model
    summary="Get patterns awaiting review",
)
async def get_patterns_awaiting_review_endpoint(
    reviewer_id: Optional[str] = Depends(
        get_current_user_id
    ),  # Default to current user
    workflow_manager: WorkflowManager = Depends(get_workflow_manager),
    user_roles: list[str] = Depends(get_current_user_roles),
):
    """
    Retrieves a list of patterns that are currently in the 'in_review' state
    and are awaiting feedback, optionally filtered by a specific reviewer.
    Admins can see all pending reviews.
    """
    # If user is admin, they can see all pending reviews, otherwise only their own.
    if "admin" in user_roles:
        reviewer_id_filter = None
    else:
        reviewer_id_filter = reviewer_id

    try:
        pending_patterns = await workflow_manager.get_patterns_awaiting_review(
            reviewer_id_filter
        )
        return pending_patterns
    except Exception as e:
        logger.error(f"Error getting pending reviews: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve pending reviews: {str(e)}",
        )
