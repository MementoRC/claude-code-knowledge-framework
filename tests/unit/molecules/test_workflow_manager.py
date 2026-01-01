import datetime
import json
from typing import Any  # Added missing imports
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.uckn.api.models.patterns import (
    Pattern,
    PatternMetadata,
    PatternStatus,
    SharingScope,
    TechnologyStackDNA,
)
from src.uckn.api.models.workflow import (
    InitiateReviewRequest,
    PatternVersion,
    ReviewFeedback,
    ReviewStatus,
    SubmitReviewFeedbackRequest,
    WorkflowState,
    WorkflowTransitionRequest,
)
from src.uckn.api.routers.collaboration import ConnectionManager  # Import for mocking
from src.uckn.core.molecules.workflow_manager import WorkflowManager


# Mock KnowledgeManager and ConnectionManager
@pytest.fixture
def mock_knowledge_manager():
    km = MagicMock()
    km.get_pattern = MagicMock(return_value=None)  # Default to no pattern found
    km.update_pattern = MagicMock(return_value=True)
    km.add_pattern = MagicMock(return_value="new_pattern_id")
    km.get_all_patterns_by_status = MagicMock(return_value=[])
    return km


@pytest.fixture
def mock_connection_manager():
    cm = MagicMock(spec=ConnectionManager)
    cm.broadcast = AsyncMock()
    cm.send_personal_message = AsyncMock()
    return cm


@pytest.fixture
def workflow_manager(mock_knowledge_manager, mock_connection_manager):
    return WorkflowManager(mock_knowledge_manager, mock_connection_manager)


# Helper to create a mock pattern object (as a dictionary, as KM returns dicts)
def create_mock_pattern_dict(
    pattern_id: str,
    status: PatternStatus,
    current_version: str = "1.0.0",
    versions: list[PatternVersion] | None = None,
    reviews: list[ReviewFeedback] | None = None,
    document: str = "test document content",
    title: str = "Test Pattern",
) -> dict[str, Any]:
    if versions is None:
        versions = [
            PatternVersion(
                version_number="0.1.0",
                changes="Initial draft",
                timestamp=datetime.datetime.now() - datetime.timedelta(days=1),
                author_id="author1",
                document_hash="initial_hash",
                status_at_creation=PatternStatus.DRAFT,
            )
        ]
    if reviews is None:
        reviews = []

    # Convert Pydantic models to dictionaries for the mock KM return value
    return Pattern(
        id=pattern_id,
        document=document,
        metadata=PatternMetadata(
            title=title,
            description="A test pattern.",
            pattern_type="code_snippet",
            technology_stack=TechnologyStackDNA(
                confidence_score=1.0
            ),  # Added confidence_score
            author="author1",
        ),
        sharing_scope=SharingScope.PRIVATE,
        status=status,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        current_version=current_version,
        versions=versions,
        reviews=reviews,
    ).dict(by_alias=True)


@pytest.mark.asyncio
async def test_initiate_review_success(
    workflow_manager, mock_knowledge_manager, mock_connection_manager
):
    pattern_id = "pat123"
    mock_pattern_dict = create_mock_pattern_dict(
        pattern_id, PatternStatus.DRAFT, current_version="0.1.0"
    )
    mock_knowledge_manager.get_pattern.return_value = mock_pattern_dict

    request = InitiateReviewRequest(
        reviewer_ids=["reviewer1", "reviewer2"],
        message="Please review this new pattern.",
    )
    user_id = "author1"

    response = await workflow_manager.initiate_review(pattern_id, request, user_id)

    assert response["status"] == "success"
    assert response["new_state"] == WorkflowState.IN_REVIEW
    assert response["new_version"] == "0.2.0"  # Minor version increment

    mock_knowledge_manager.update_pattern.assert_called_once()
    # The update_pattern method receives a dict (converted from Pattern via .dict())
    updated_pattern_dict = mock_knowledge_manager.update_pattern.call_args[0][1]
    assert updated_pattern_dict["status"] == WorkflowState.IN_REVIEW.value
    assert updated_pattern_dict["current_version"] == "0.2.0"
    assert len(updated_pattern_dict["reviews"]) == 2
    assert updated_pattern_dict["reviews"][0]["reviewer_id"] == "reviewer1"
    assert updated_pattern_dict["reviews"][0]["status"] == ReviewStatus.PENDING.value
    assert updated_pattern_dict["reviews"][0]["version"] == "0.2.0"
    assert len(updated_pattern_dict["versions"]) == 2  # Original + new version
    assert updated_pattern_dict["versions"][-1]["version_number"] == "0.2.0"

    mock_connection_manager.broadcast.assert_called_once()
    broadcast_message = json.loads(mock_connection_manager.broadcast.call_args[0][0])
    assert broadcast_message["type"] == "pattern_submitted_for_review"
    assert broadcast_message["pattern_id"] == pattern_id
    assert broadcast_message["new_state"] == WorkflowState.IN_REVIEW.value


@pytest.mark.asyncio
async def test_initiate_review_not_draft_fails(
    workflow_manager, mock_knowledge_manager
):
    pattern_id = "pat123"
    mock_pattern_dict = create_mock_pattern_dict(pattern_id, PatternStatus.PUBLISHED)
    mock_knowledge_manager.get_pattern.return_value = mock_pattern_dict

    request = InitiateReviewRequest(reviewer_ids=["reviewer1"])
    user_id = "author1"

    with pytest.raises(ValueError, match="Pattern is not in DRAFT state"):
        await workflow_manager.initiate_review(pattern_id, request, user_id)

    mock_knowledge_manager.update_pattern.assert_not_called()


@pytest.mark.asyncio
async def test_submit_review_feedback_success(
    workflow_manager, mock_knowledge_manager, mock_connection_manager
):
    pattern_id = "pat123"
    mock_pattern_dict = create_mock_pattern_dict(
        pattern_id,
        PatternStatus.IN_REVIEW,
        current_version="0.2.0",
        reviews=[
            ReviewFeedback(
                reviewer_id="reviewer1", status=ReviewStatus.PENDING, version="0.2.0"
            ),
            ReviewFeedback(
                reviewer_id="reviewer2", status=ReviewStatus.PENDING, version="0.2.0"
            ),
        ],
    )
    mock_knowledge_manager.get_pattern.return_value = mock_pattern_dict

    request = SubmitReviewFeedbackRequest(
        reviewer_id="reviewer1",
        comments="Looks good, minor tweaks needed.",
        score=4.5,
        status=ReviewStatus.NEEDS_REVISION,
        version="0.2.0",
    )

    response = await workflow_manager.submit_review_feedback(pattern_id, request)

    assert response["status"] == "success"
    mock_knowledge_manager.update_pattern.assert_called_once()
    updated_pattern_dict = mock_knowledge_manager.update_pattern.call_args[0][1]

    reviewer1_feedback = next(
        r for r in updated_pattern_dict["reviews"] if r["reviewer_id"] == "reviewer1"
    )
    assert reviewer1_feedback["status"] == ReviewStatus.NEEDS_REVISION.value
    assert reviewer1_feedback["comments"] == "Looks good, minor tweaks needed."
    assert reviewer1_feedback["score"] == 4.5

    mock_connection_manager.broadcast.assert_called_once()
    broadcast_message = json.loads(mock_connection_manager.broadcast.call_args[0][0])
    assert broadcast_message["type"] == "pattern_review_feedback_submitted"


@pytest.mark.asyncio
async def test_transition_state_approve_review_success(
    workflow_manager, mock_knowledge_manager, mock_connection_manager
):
    pattern_id = "pat123"
    mock_pattern_dict = create_mock_pattern_dict(
        pattern_id,
        PatternStatus.IN_REVIEW,
        current_version="0.2.0",
        reviews=[
            ReviewFeedback(
                reviewer_id="reviewer1", status=ReviewStatus.APPROVED, version="0.2.0"
            ),
            ReviewFeedback(
                reviewer_id="reviewer2", status=ReviewStatus.APPROVED, version="0.2.0"
            ),
        ],
    )
    mock_knowledge_manager.get_pattern.return_value = mock_pattern_dict

    request = WorkflowTransitionRequest(
        target_state=WorkflowState.IN_TESTING,
        comments="All reviews approved, moving to testing.",
        user_id="admin_user",
        version="0.2.0",
    )

    response = await workflow_manager.transition_state(pattern_id, request)

    assert response["status"] == "success"
    assert response["new_state"] == WorkflowState.IN_TESTING
    mock_knowledge_manager.update_pattern.assert_called_once()
    updated_pattern_dict = mock_knowledge_manager.update_pattern.call_args[0][1]
    assert updated_pattern_dict["status"] == WorkflowState.IN_TESTING.value
    mock_connection_manager.broadcast.assert_called_once()
    broadcast_message = json.loads(mock_connection_manager.broadcast.call_args[0][0])
    assert broadcast_message["type"] == "pattern_approved_for_testing"


@pytest.mark.asyncio
async def test_transition_state_publish_success(
    workflow_manager, mock_knowledge_manager, mock_connection_manager
):
    pattern_id = "pat123"
    mock_pattern_dict = create_mock_pattern_dict(
        pattern_id,
        PatternStatus.APPROVED_FOR_PUBLISH,
        current_version="0.2.0",
        document="published content",
    )
    mock_knowledge_manager.get_pattern.return_value = mock_pattern_dict

    request = WorkflowTransitionRequest(
        target_state=WorkflowState.PUBLISHED,
        comments="Ready for production.",
        user_id="admin_user",
        version="0.2.0",
    )

    response = await workflow_manager.transition_state(pattern_id, request)

    assert response["status"] == "success"
    assert response["new_state"] == WorkflowState.PUBLISHED
    assert response["new_version"] == "1.0.0"  # Major version increment for publish

    mock_knowledge_manager.update_pattern.assert_called_once()
    updated_pattern_dict = mock_knowledge_manager.update_pattern.call_args[0][1]
    assert updated_pattern_dict["status"] == WorkflowState.PUBLISHED.value
    assert updated_pattern_dict["current_version"] == "1.0.0"
    assert len(updated_pattern_dict["versions"]) == 2  # Original 0.1.0 + new 1.0.0
    assert updated_pattern_dict["versions"][-1]["version_number"] == "1.0.0"
    assert (
        updated_pattern_dict["versions"][-1]["status_at_creation"]
        == WorkflowState.PUBLISHED.value
    )

    mock_connection_manager.broadcast.assert_called_once()
    broadcast_message = json.loads(mock_connection_manager.broadcast.call_args[0][0])
    assert broadcast_message["type"] == "pattern_published"


@pytest.mark.asyncio
async def test_get_workflow_status(workflow_manager, mock_knowledge_manager):
    pattern_id = "pat123"
    mock_pattern_dict = create_mock_pattern_dict(
        pattern_id,
        PatternStatus.IN_REVIEW,
        current_version="0.2.0",
        versions=[
            PatternVersion(
                version_number="0.1.0",
                changes="initial",
                timestamp=datetime.datetime.now() - datetime.timedelta(days=2),
                author_id="a",
                document_hash="h1",
                status_at_creation=PatternStatus.DRAFT,
            ),
            PatternVersion(
                version_number="0.2.0",
                changes="review",
                timestamp=datetime.datetime.now() - datetime.timedelta(days=1),
                author_id="a",
                document_hash="h2",
                status_at_creation=PatternStatus.IN_REVIEW,
            ),
        ],
        reviews=[
            ReviewFeedback(
                reviewer_id="r1",
                status=ReviewStatus.PENDING,
                version="0.2.0",
                timestamp=datetime.datetime.now(),
            ),
            ReviewFeedback(
                reviewer_id="r2",
                status=ReviewStatus.APPROVED,
                version="0.1.0",
                timestamp=datetime.datetime.now() - datetime.timedelta(days=3),
            ),
        ],
    )
    mock_knowledge_manager.get_pattern.return_value = mock_pattern_dict

    status_response = await workflow_manager.get_workflow_status(pattern_id)

    assert status_response["pattern_id"] == pattern_id
    assert status_response["current_state"] == WorkflowState.IN_REVIEW
    assert status_response["current_version"] == "0.2.0"
    assert len(status_response["pending_reviews"]) == 1
    assert status_response["pending_reviews"][0].reviewer_id == "r1"
    assert status_response["pending_reviews"][0].status == ReviewStatus.PENDING
    assert len(status_response["review_history"]) == 2
    assert len(status_response["version_history"]) == 2


@pytest.mark.asyncio
async def test_get_patterns_awaiting_review(workflow_manager, mock_knowledge_manager):
    pattern1_dict = create_mock_pattern_dict(
        "pat1",
        PatternStatus.IN_REVIEW,
        current_version="0.2.0",
        reviews=[
            ReviewFeedback(
                reviewer_id="reviewerA", status=ReviewStatus.PENDING, version="0.2.0"
            )
        ],
    )
    pattern2_dict = create_mock_pattern_dict(
        "pat2",
        PatternStatus.IN_REVIEW,
        current_version="0.3.0",
        reviews=[
            ReviewFeedback(
                reviewer_id="reviewerB", status=ReviewStatus.PENDING, version="0.3.0"
            )
        ],
    )
    pattern3_dict = create_mock_pattern_dict(
        "pat3", PatternStatus.PUBLISHED
    )  # Not in review

    mock_knowledge_manager.get_all_patterns_by_status.return_value = [
        pattern1_dict,
        pattern2_dict,
        pattern3_dict,
    ]

    # Test for all pending reviews (admin view)
    all_pending = await workflow_manager.get_patterns_awaiting_review(reviewer_id=None)
    assert len(all_pending) == 2
    assert {p["pattern_id"] for p in all_pending} == {"pat1", "pat2"}

    # Test for specific reviewer
    reviewer_a_pending = await workflow_manager.get_patterns_awaiting_review(
        reviewer_id="reviewerA"
    )
    assert len(reviewer_a_pending) == 1
    assert reviewer_a_pending[0]["pattern_id"] == "pat1"
    assert reviewer_a_pending[0]["assigned_reviewer"] == "reviewerA"

    reviewer_c_pending = await workflow_manager.get_patterns_awaiting_review(
        reviewer_id="reviewerC"
    )
    assert len(reviewer_c_pending) == 0
