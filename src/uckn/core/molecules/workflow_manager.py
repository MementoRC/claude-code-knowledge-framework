from __future__ import annotations

import datetime
import hashlib
import json
import logging
from typing import TYPE_CHECKING, Any, Optional

from pydantic import ValidationError

from ..organisms.knowledge_manager import KnowledgeManager

if TYPE_CHECKING:
    from ...api.models.patterns import Pattern
    from ...api.models.workflow import (
        InitiateReviewRequest,
        SubmitReviewFeedbackRequest,
        WorkflowState,
        WorkflowTransitionRequest,
    )

logger = logging.getLogger(__name__)


class WorkflowManager:
    """
    Manages the lifecycle and state transitions of knowledge patterns.
    Implements a state machine for pattern contribution, review, and publishing.
    """

    # Define allowed state transitions using string values for states
    # (current_state_str, action) -> (next_state_str, required_role, notification_type)
    # Actions: 'submit_for_review', 'submit_feedback', 'approve_review', 'reject_review',
    # 'approve_testing', 'reject_testing', 'publish', 'retire', 'deprecate', 'reactivate', 'needs_revision', 'resubmit'
    STATE_TRANSITIONS = {
        ("draft", "submit_for_review"): (
            "in_review",
            "contributor",
            "pattern_submitted_for_review",
        ),
        ("in_review", "approve_review"): (
            "in_testing",
            "admin",
            "pattern_approved_for_testing",
        ),  # Requires all reviews to be approved
        ("in_review", "reject_review"): ("rejected", "admin", "pattern_rejected"),
        ("in_review", "needs_revision"): (
            "draft",
            "admin",
            "pattern_needs_revision",
        ),  # Back to draft for author
        ("in_testing", "approve_testing"): (
            "approved_for_publish",
            "admin",
            "pattern_approved_for_publish",
        ),
        ("in_testing", "reject_testing"): ("rejected", "admin", "pattern_rejected"),
        ("in_testing", "needs_revision"): (
            "draft",
            "admin",
            "pattern_needs_revision",
        ),  # Back to draft for author
        ("approved_for_publish", "publish"): (
            "published",
            "admin",
            "pattern_published",
        ),
        ("published", "update_draft"): (
            "draft",
            "contributor",
            "pattern_update_draft_created",
        ),  # Creates new draft version
        ("published", "retire"): ("maintenance", "admin", "pattern_retired"),
        ("maintenance", "deprecate"): ("deprecated", "admin", "pattern_deprecated"),
        ("maintenance", "reactivate"): ("published", "admin", "pattern_reactivated"),
        ("rejected", "resubmit"): ("draft", "contributor", "pattern_resubmitted"),
        ("deprecated", "reactivate"): ("maintenance", "admin", "pattern_reactivated"),
    }

    def __init__(self, knowledge_manager: KnowledgeManager, connection_manager: Any):
        self.knowledge_manager = knowledge_manager
        self.connection_manager = connection_manager

    async def _get_pattern(self, pattern_id: str) -> Optional[Pattern]:  # noqa: F821
        """Helper to retrieve a pattern and convert it to Pydantic model."""
        # Lazy imports
        from ...api.models.patterns import Pattern, PatternMetadata
        from ...api.models.workflow import PatternVersion, ReviewFeedback

        pattern_data = self.knowledge_manager.get_pattern(pattern_id)
        if pattern_data:
            try:
                # Ensure nested Pydantic models are correctly initialized from dicts
                if "metadata" in pattern_data and isinstance(
                    pattern_data["metadata"], dict
                ):
                    pattern_data["metadata"] = PatternMetadata(
                        **pattern_data["metadata"]
                    )
                if "versions" in pattern_data:
                    pattern_data["versions"] = [
                        PatternVersion(**v) for v in pattern_data["versions"]
                    ]
                if "reviews" in pattern_data:
                    pattern_data["reviews"] = [
                        ReviewFeedback(**r) for r in pattern_data["reviews"]
                    ]

                return Pattern(**pattern_data)
            except ValidationError as e:
                logger.error(f"Failed to validate pattern {pattern_id} from DB: {e}")
                return None
        return None

    async def _update_pattern_in_db(
        self, pattern_id: str, pattern_model: Pattern
    ) -> bool:  # noqa: F821
        """Helper to update pattern in the database, converting Pydantic model to dict."""
        # Convert Pydantic model back to dictionary, handling nested models
        updates = pattern_model.dict(by_alias=True)
        return self.knowledge_manager.update_pattern(pattern_id, updates)

    async def _broadcast_workflow_update(
        self,
        pattern_id: str,
        new_state: WorkflowState,
        message_type: str,
        user_id: str,
        version: str,
    ):  # noqa: F821
        """Broadcasts a workflow state change via WebSocket."""
        # Lazy import (though ConnectionManager instance is passed in __init__)
        # This import is here to satisfy the request to import ConnectionManager only when needed.

        update_message = {
            "type": message_type,
            "pattern_id": pattern_id,
            "new_state": new_state.value,
            "user_id": user_id,
            "version": version,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        await self.connection_manager.broadcast(json.dumps(update_message))

    async def initiate_review(
        self, pattern_id: str, request: InitiateReviewRequest, user_id: str
    ) -> dict[str, Any]:  # noqa: F821
        """Initiates the review process for a pattern."""
        # Lazy imports
        from ...api.models.workflow import (
            PatternVersion,
            ReviewFeedback,
            ReviewStatus,
            WorkflowState,
        )

        pattern = await self._get_pattern(pattern_id)
        if not pattern:
            raise ValueError("Pattern not found.")

        if pattern.status != WorkflowState.DRAFT:
            raise ValueError(
                f"Pattern is not in DRAFT state. Current state: {pattern.status.value}"
            )

        # Determine new version number and create new version entry
        current_doc_hash = hashlib.sha256(pattern.document.encode("utf-8")).hexdigest()

        new_version_number = pattern.current_version
        # If document changed or it's the very first submission for review, increment minor version
        if (
            not pattern.versions
            or pattern.versions[-1].document_hash != current_doc_hash
            or pattern.status == WorkflowState.DRAFT
        ):
            parts = [int(x) for x in pattern.current_version.split(".")]
            parts[1] += 1  # Increment minor version for new review submission
            parts[2] = 0  # Reset patch version
            new_version_number = ".".join(map(str, parts))

            new_version = PatternVersion(
                version_number=new_version_number,
                changes=request.message
                or f"Submitted for review (version {new_version_number})",
                author_id=user_id,
                document_hash=current_doc_hash,
                status_at_creation=WorkflowState.IN_REVIEW,
            )
            pattern.versions.append(new_version)
            pattern.current_version = new_version_number
        else:
            # If document hasn't changed and it's already been reviewed, just re-assign reviews
            logger.info(
                f"Document for pattern {pattern_id} has not changed. Re-initiating review for current version {pattern.current_version}."
            )

        # Clear existing pending reviews for this version and add new pending ones
        pattern.reviews = [
            rf
            for rf in pattern.reviews
            if not (
                rf.version == pattern.current_version
                and rf.status == ReviewStatus.PENDING
            )
        ]
        for reviewer_id in request.reviewer_ids:
            pattern.reviews.append(
                ReviewFeedback(
                    reviewer_id=reviewer_id,
                    status=ReviewStatus.PENDING,
                    version=pattern.current_version,
                    comments=request.message,
                )
            )

        # Transition state
        # Use .value to get string for lookup in STATE_TRANSITIONS
        next_state_str, _, notification_type = self.STATE_TRANSITIONS.get(
            (pattern.status.value, "submit_for_review"), (None, None, None)
        )
        if not next_state_str:
            raise ValueError(
                f"Invalid state transition from {pattern.status.value} with action 'submit_for_review'."
            )

        pattern.status = WorkflowState(
            next_state_str
        )  # Convert string back to enum for assignment
        pattern.updated_at = datetime.datetime.now()
        pattern.updated_by = user_id

        success = await self._update_pattern_in_db(pattern_id, pattern)
        if not success:
            raise RuntimeError("Failed to update pattern in database.")

        await self._broadcast_workflow_update(
            pattern_id,
            pattern.status,
            notification_type,
            user_id,
            pattern.current_version,
        )

        return {
            "pattern_id": pattern_id,
            "status": "success",
            "message": f"Pattern submitted for review. Current state: {pattern.status.value}",
            "new_state": pattern.status,
            "new_version": pattern.current_version,
        }

    async def submit_review_feedback(
        self, pattern_id: str, request: SubmitReviewFeedbackRequest
    ) -> dict[str, Any]:  # noqa: F821
        """Submits review feedback for a pattern."""
        # Lazy imports
        from ...api.models.workflow import ReviewFeedback, WorkflowState

        pattern = await self._get_pattern(pattern_id)
        if not pattern:
            raise ValueError("Pattern not found.")

        if pattern.status not in [WorkflowState.IN_REVIEW, WorkflowState.IN_TESTING]:
            raise ValueError(
                f"Pattern is not in review or testing state. Current state: {pattern.status.value}"
            )

        # Find and update the specific review entry for the given reviewer and version
        found_review_index = -1
        for i, review in enumerate(pattern.reviews):
            if (
                review.reviewer_id == request.reviewer_id
                and review.version == request.version
            ):
                found_review_index = i
                break

        new_feedback = ReviewFeedback(
            reviewer_id=request.reviewer_id,
            timestamp=datetime.datetime.now(),
            comments=request.comments,
            score=request.score,
            status=request.status,
            version=request.version,
        )

        if found_review_index != -1:
            pattern.reviews[found_review_index] = new_feedback
        else:
            # If no existing review, add it (e.g., for ad-hoc feedback or if reviewer was added later)
            pattern.reviews.append(new_feedback)
            logger.warning(
                f"No pending review found for reviewer {request.reviewer_id} on pattern {pattern_id} version {request.version}. Adding as new feedback."
            )

        pattern.updated_at = datetime.datetime.now()
        pattern.updated_by = request.reviewer_id

        success = await self._update_pattern_in_db(pattern_id, pattern)
        if not success:
            raise RuntimeError("Failed to update pattern in database.")

        # Broadcast feedback update (optional, could be more granular)
        await self._broadcast_workflow_update(
            pattern_id,
            pattern.status,
            "pattern_review_feedback_submitted",
            request.reviewer_id,
            request.version,
        )

        return {
            "pattern_id": pattern_id,
            "status": "success",
            "message": "Review feedback submitted successfully.",
        }

    async def transition_state(
        self, pattern_id: str, request: WorkflowTransitionRequest
    ) -> dict[str, Any]:  # noqa: F821
        """Transitions a pattern to a new workflow state."""
        # Lazy imports
        from ...api.models.workflow import PatternVersion, ReviewStatus, WorkflowState

        pattern = await self._get_pattern(pattern_id)
        if not pattern:
            raise ValueError("Pattern not found.")

        current_state = pattern.status
        target_state = request.target_state
        action = None  # Determine action based on target state and current state

        # Map target state to an internal action for STATE_TRANSITIONS
        if (
            target_state == WorkflowState.IN_REVIEW
            and current_state == WorkflowState.DRAFT
        ):
            action = "submit_for_review"  # This action is handled by initiate_review, so this path might be redundant
        elif (
            target_state == WorkflowState.IN_TESTING
            and current_state == WorkflowState.IN_REVIEW
        ):
            # Check if all reviews are approved for the current version
            current_version_reviews = [
                r for r in pattern.reviews if r.version == pattern.current_version
            ]
            if not current_version_reviews:
                raise ValueError(
                    "No reviews submitted for the current version to transition to testing."
                )
            if not all(
                r.status == ReviewStatus.APPROVED for r in current_version_reviews
            ):
                raise ValueError(
                    "Not all reviews are approved for the current version to move to testing."
                )
            action = "approve_review"
        elif (
            target_state == WorkflowState.APPROVED_FOR_PUBLISH
            and current_state == WorkflowState.IN_TESTING
        ):
            action = "approve_testing"
        elif (
            target_state == WorkflowState.PUBLISHED
            and current_state == WorkflowState.APPROVED_FOR_PUBLISH
        ):
            action = "publish"
        elif target_state == WorkflowState.DRAFT and current_state in [
            WorkflowState.IN_REVIEW,
            WorkflowState.IN_TESTING,
            WorkflowState.REJECTED,
        ]:
            action = (
                "needs_revision"
                if current_state in [WorkflowState.IN_REVIEW, WorkflowState.IN_TESTING]
                else "resubmit"
            )
        elif target_state == WorkflowState.REJECTED and current_state in [
            WorkflowState.IN_REVIEW,
            WorkflowState.IN_TESTING,
        ]:
            action = (
                "reject_review"
                if current_state == WorkflowState.IN_REVIEW
                else "reject_testing"
            )
        elif (
            target_state == WorkflowState.MAINTENANCE
            and current_state == WorkflowState.PUBLISHED
        ):
            action = "retire"
        elif (
            target_state == WorkflowState.DEPRECATED
            and current_state == WorkflowState.MAINTENANCE
        ):
            action = "deprecate"
        elif target_state == WorkflowState.PUBLISHED and current_state in [
            WorkflowState.MAINTENANCE,
            WorkflowState.DEPRECATED,
        ]:
            action = "reactivate"
        else:
            raise ValueError(
                f"Invalid or unsupported transition from {current_state.value} to {target_state.value}."
            )

        # Use .value to get string for lookup in STATE_TRANSITIONS
        next_state_str, required_role, notification_type = self.STATE_TRANSITIONS.get(
            (current_state.value, action), (None, None, None)
        )

        # Convert string back to WorkflowState enum for comparison
        if not next_state_str or WorkflowState(next_state_str) != target_state:
            raise ValueError(
                f"Invalid state transition from {current_state.value} with action '{action}' to {target_state.value}."
            )

        # TODO: Implement role-based access control here using 'required_role'
        # For now, assuming user_id has necessary permissions as checked in router.

        pattern.status = WorkflowState(next_state_str)  # Assign the enum member
        pattern.updated_at = datetime.datetime.now()
        pattern.updated_by = request.user_id

        # If publishing, ensure a new version is recorded if not already
        if pattern.status == WorkflowState.PUBLISHED:
            current_doc_hash = hashlib.sha256(
                pattern.document.encode("utf-8")
            ).hexdigest()
            # Check if the latest version in history is already PUBLISHED and has the same content
            is_latest_published_and_same_content = (
                pattern.versions
                and pattern.versions[-1].status_at_creation == WorkflowState.PUBLISHED
                and pattern.versions[-1].document_hash == current_doc_hash
            )

            if not is_latest_published_and_same_content:
                # Increment major version for publishing a new significant version
                parts = [int(x) for x in pattern.current_version.split(".")]
                parts[0] += 1  # Increment major version
                parts[1] = 0
                parts[2] = 0
                new_version_number = ".".join(map(str, parts))

                new_version = PatternVersion(
                    version_number=new_version_number,
                    changes=request.comments
                    or f"Published version {new_version_number}",
                    author_id=request.user_id,
                    document_hash=current_doc_hash,
                    status_at_creation=WorkflowState.PUBLISHED,
                )
                pattern.versions.append(new_version)
                pattern.current_version = new_version_number
            else:
                new_version_number = (
                    pattern.current_version
                )  # No new version if already published and no changes

        success = await self._update_pattern_in_db(pattern_id, pattern)
        if not success:
            raise RuntimeError("Failed to update pattern in database.")

        await self._broadcast_workflow_update(
            pattern_id,
            pattern.status,
            notification_type,
            request.user_id,
            pattern.current_version,
        )

        return {
            "pattern_id": pattern_id,
            "status": "success",
            "message": f"Pattern state transitioned to {pattern.status.value}.",
            "new_state": pattern.status,
            "new_version": pattern.current_version,
        }

    async def get_workflow_status(self, pattern_id: str) -> dict[str, Any]:
        """Retrieves the current workflow status of a pattern."""
        # Lazy imports
        from ...api.models.workflow import ReviewStatus

        pattern = await self._get_pattern(pattern_id)
        if not pattern:
            raise ValueError("Pattern not found.")

        # Filter reviews for pending ones for the current version
        pending_reviews = [
            r
            for r in pattern.reviews
            if r.status == ReviewStatus.PENDING and r.version == pattern.current_version
        ]

        # All reviews for history, sorted by timestamp
        review_history = sorted(pattern.reviews, key=lambda r: r.timestamp)

        # Version history, sorted by timestamp
        version_history = sorted(pattern.versions, key=lambda v: v.timestamp)

        return {
            "pattern_id": pattern.id,
            "current_state": pattern.status,
            "current_version": pattern.current_version,
            "pending_reviews": pending_reviews,
            "review_history": review_history,
            "version_history": version_history,
            "last_transition_at": pattern.updated_at,
            "last_transition_by": pattern.updated_by,
        }

    async def get_patterns_awaiting_review(
        self, reviewer_id: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Retrieves patterns that are in IN_REVIEW state and optionally assigned to a specific reviewer.
        This requires KnowledgeManager to support searching by nested fields or iterating.
        For now, a simplified approach assuming KnowledgeManager can return patterns by status.
        """
        # Lazy imports
        from ...api.models.patterns import Pattern
        from ...api.models.workflow import ReviewStatus, WorkflowState

        # This is a placeholder. A real implementation would query the DB efficiently.
        # Assuming KnowledgeManager can return all patterns or patterns by status.
        # The `get_all_patterns_by_status` method is an assumption for KnowledgeManager.
        all_patterns_data = self.knowledge_manager.get_all_patterns_by_status(
            WorkflowState.IN_REVIEW.value
        )

        pending_patterns_summary = []
        for p_data in all_patterns_data:
            try:
                pattern = Pattern(**p_data)
                # Check if there's a pending review for the current version for this reviewer
                if pattern.status == WorkflowState.IN_REVIEW:
                    for review in pattern.reviews:
                        if (
                            review.version == pattern.current_version
                            and review.status == ReviewStatus.PENDING
                        ):
                            if reviewer_id is None or review.reviewer_id == reviewer_id:
                                pending_patterns_summary.append(
                                    {
                                        "pattern_id": pattern.id,
                                        "title": pattern.metadata.title,
                                        "current_version": pattern.current_version,
                                        "assigned_reviewer": review.reviewer_id,
                                        "review_status": review.status.value,
                                        "submitted_at": pattern.updated_at,  # Or review.timestamp
                                    }
                                )
                                break  # Only add once per pattern to the summary list
            except ValidationError as e:
                logger.warning(
                    f"Skipping malformed pattern during pending review check: {p_data.get('id', 'N/A')}, Error: {e}"
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error processing pattern {p_data.get('id', 'N/A')}: {e}"
                )
        return pending_patterns_summary
