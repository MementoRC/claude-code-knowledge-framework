import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class WorkflowState(str, Enum):
    """Defines the states in the pattern contribution workflow."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    IN_TESTING = "in_testing"
    APPROVED_FOR_PUBLISH = "approved_for_publish"
    PUBLISHED = "published"
    MAINTENANCE = "maintenance"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


class ReviewStatus(str, Enum):
    """Status of a single review."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class ReviewFeedback(BaseModel):
    """Model for a single review feedback entry."""

    reviewer_id: str = Field(description="ID of the reviewer")
    timestamp: datetime.datetime = Field(
        default_factory=datetime.datetime.now, description="Timestamp of the review"
    )
    comments: Optional[str] = Field(default=None, description="Review comments")
    score: Optional[float] = Field(
        default=None, ge=0.0, le=5.0, description="Overall review score (0-5)"
    )
    status: ReviewStatus = Field(
        description="Status of the review (approved, rejected, needs_revision)"
    )
    version: str = Field(description="Version of the pattern being reviewed")


class PatternVersion(BaseModel):
    """Model for tracking pattern versions."""

    version_number: str = Field(description="Semantic version number (e.g., 1.0.0)")
    changes: str = Field(description="Description of changes in this version")
    timestamp: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description="Timestamp of this version creation",
    )
    author_id: str = Field(description="ID of the user who created this version")
    document_hash: str = Field(
        description="Hash of the pattern document for integrity check"
    )
    status_at_creation: WorkflowState = Field(
        description="Workflow state when this version was created"
    )


class WorkflowTransitionRequest(BaseModel):
    """Request model for transitioning a pattern's workflow state."""

    target_state: WorkflowState = Field(description="The target workflow state")
    comments: Optional[str] = Field(
        default=None, description="Comments for the state transition"
    )
    user_id: str = Field(
        description="ID of the user performing the transition"
    )  # Will be overridden by authenticated user_id in router
    version: Optional[str] = Field(
        default=None, description="Specific version to transition, if applicable"
    )


class WorkflowStatusResponse(BaseModel):
    """Response model for retrieving a pattern's workflow status."""

    pattern_id: str = Field(description="ID of the pattern")
    current_state: WorkflowState = Field(description="Current workflow state")
    current_version: str = Field(description="Current active version number")
    pending_reviews: list[ReviewFeedback] = Field(
        default_factory=list,
        description="List of pending review requests for the current version",
    )
    review_history: list[ReviewFeedback] = Field(
        default_factory=list,
        description="History of all submitted reviews across versions",
    )
    version_history: list[PatternVersion] = Field(
        default_factory=list, description="History of all pattern versions"
    )
    last_transition_at: Optional[datetime.datetime] = Field(
        default=None, description="Timestamp of the last state transition"
    )
    last_transition_by: Optional[str] = Field(
        default=None, description="User who performed the last transition"
    )


class SubmitReviewFeedbackRequest(BaseModel):
    """Request model for submitting review feedback."""

    reviewer_id: str = Field(description="ID of the reviewer submitting feedback")
    comments: Optional[str] = Field(default=None, description="Review comments")
    score: Optional[float] = Field(
        default=None, ge=0.0, le=5.0, description="Overall review score (0-5)"
    )
    status: ReviewStatus = Field(
        description="Status of the review (approved, rejected, needs_revision)"
    )
    version: str = Field(description="Version of the pattern being reviewed")


class InitiateReviewRequest(BaseModel):
    """Request model for initiating a pattern review."""

    reviewer_ids: list[str] = Field(
        description="List of user IDs to assign as reviewers"
    )
    message: Optional[str] = Field(
        default=None, description="Optional message for reviewers"
    )
    version: Optional[str] = Field(
        default=None, description="Specific version to review, defaults to current"
    )


class WorkflowActionResponse(BaseModel):
    """Generic response for workflow actions."""

    pattern_id: str
    status: str
    message: str
    new_state: Optional[WorkflowState] = None
    new_version: Optional[str] = None
