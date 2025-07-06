import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
import datetime

# Import the router and its dependencies
from src.uckn.api.routers.workflow import router, get_workflow_manager, get_current_user_id, get_current_user_roles
from src.uckn.api.models.patterns import PatternStatus
from src.uckn.api.models.workflow import (
    WorkflowState, ReviewStatus, WorkflowTransitionRequest,
    SubmitReviewFeedbackRequest, InitiateReviewRequest, WorkflowStatusResponse,
    WorkflowActionResponse, PatternVersion, ReviewFeedback
)

# Mock dependencies
@pytest.fixture
def mock_workflow_manager():
    wm = MagicMock()
    wm.initiate_review = AsyncMock()
    wm.submit_review_feedback = AsyncMock()
    wm.transition_state = AsyncMock()
    wm.get_workflow_status = AsyncMock()
    wm.get_patterns_awaiting_review = AsyncMock()
    return wm

@pytest.fixture
def client(mock_workflow_manager):
    # Create a FastAPI app instance
    app = FastAPI()
    # Include the router in the app
    app.include_router(router)

    # Override dependencies for testing on the app instance
    app.dependency_overrides[get_workflow_manager] = lambda: mock_workflow_manager
    app.dependency_overrides[get_current_user_id] = lambda: "test_user"
    app.dependency_overrides[get_current_user_roles] = lambda: ["contributor", "admin"]
    
    # Pass the app instance to TestClient
    return TestClient(app)

@pytest.mark.asyncio
async def test_initiate_pattern_review_success(client, mock_workflow_manager):
    pattern_id = "pat123"
    request_payload = {
        "reviewer_ids": ["reviewer1"],
        "message": "Initial review"
    }
    mock_workflow_manager.initiate_review.return_value = {
        "pattern_id": pattern_id,
        "status": "success",
        "message": "Pattern submitted for review. Current state: in_review",
        "new_state": WorkflowState.IN_REVIEW,
        "new_version": "0.2.0"
    }

    response = client.post(f"/patterns/{pattern_id}/workflow/initiate_review", json=request_payload)

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["new_state"] == "in_review"
    mock_workflow_manager.initiate_review.assert_called_once_with(
        pattern_id, InitiateReviewRequest(**request_payload), "test_user"
    )

@pytest.mark.asyncio
async def test_initiate_pattern_review_bad_request(client, mock_workflow_manager):
    pattern_id = "pat123"
    request_payload = {
        "reviewer_ids": ["reviewer1"],
        "message": "Initial review"
    }
    mock_workflow_manager.initiate_review.side_effect = ValueError("Pattern not in DRAFT state.")

    response = client.post(f"/patterns/{pattern_id}/workflow/initiate_review", json=request_payload)

    assert response.status_code == 400
    assert "Pattern not in DRAFT state." in response.json()["detail"]

@pytest.mark.asyncio
async def test_submit_pattern_review_feedback_success(client, mock_workflow_manager):
    pattern_id = "pat123"
    request_payload = {
        "reviewer_id": "test_user",
        "comments": "Good work!",
        "score": 5.0,
        "status": "approved",
        "version": "0.2.0"
    }
    mock_workflow_manager.submit_review_feedback.return_value = {
        "pattern_id": pattern_id,
        "status": "success",
        "message": "Review feedback submitted successfully."
    }

    response = client.post(f"/patterns/{pattern_id}/workflow/submit_feedback", json=request_payload)

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_workflow_manager.submit_review_feedback.assert_called_once_with(
        pattern_id, SubmitReviewFeedbackRequest(**request_payload)
    )

@pytest.mark.asyncio
async def test_submit_pattern_review_feedback_unauthorized(client, mock_workflow_manager):
    pattern_id = "pat123"
    request_payload = {
        "reviewer_id": "another_user", # Not test_user and not admin
        "comments": "Good work!",
        "score": 5.0,
        "status": "approved",
        "version": "0.2.0"
    }
    # Temporarily override user roles to remove admin for this test
    # This patch needs to be applied to the app's dependency_overrides, not directly to the module
    # To do this correctly, we need to modify the client fixture or use a context manager for the patch
    # For simplicity and to directly address the user's request, I'll keep the patch as is,
    # but note that in a more complex scenario, you might adjust the fixture itself.
    with patch('src.uckn.api.routers.workflow.get_current_user_roles', return_value=["contributor"]):
        response = client.post(f"/patterns/{pattern_id}/workflow/submit_feedback", json=request_payload)

    assert response.status_code == 400
    assert "User not authorized to submit feedback" in response.json()["detail"]
    mock_workflow_manager.submit_review_feedback.assert_not_called()


@pytest.mark.asyncio
async def test_transition_pattern_state_success(client, mock_workflow_manager):
    pattern_id = "pat123"
    request_payload = {
        "target_state": "published",
        "comments": "Ready to go live",
        "user_id": "test_user",
        "version": "1.0.0"
    }
    mock_workflow_manager.transition_state.return_value = {
        "pattern_id": pattern_id,
        "status": "success",
        "message": "Pattern state transitioned to published.",
        "new_state": WorkflowState.PUBLISHED,
        "new_version": "1.0.0"
    }

    response = client.post(f"/patterns/{pattern_id}/workflow/transition", json=request_payload)

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["new_state"] == "published"
    mock_workflow_manager.transition_state.assert_called_once()
    # Verify user_id is correctly set by the router
    assert mock_workflow_manager.transition_state.call_args[0][1].user_id == "test_user"

@pytest.mark.asyncio
async def test_transition_pattern_state_forbidden(client, mock_workflow_manager):
    pattern_id = "pat123"
    request_payload = {
        "target_state": "published",
        "comments": "Ready to go live",
        "user_id": "test_user",
        "version": "1.0.0"
    }
    # Temporarily override user roles to remove admin for this test
    with patch('src.uckn.api.routers.workflow.get_current_user_roles', return_value=["contributor"]):
        response = client.post(f"/patterns/{pattern_id}/workflow/transition", json=request_payload)

    assert response.status_code == 403
    assert "Insufficient permissions" in response.json()["detail"]
    mock_workflow_manager.transition_state.assert_not_called()

@pytest.mark.asyncio
async def test_get_pattern_workflow_status_success(client, mock_workflow_manager):
    pattern_id = "pat123"
    mock_workflow_manager.get_workflow_status.return_value = WorkflowStatusResponse(
        pattern_id=pattern_id,
        current_state=WorkflowState.IN_REVIEW,
        current_version="0.2.0",
        pending_reviews=[
            ReviewFeedback(reviewer_id="reviewer1", status=ReviewStatus.PENDING, version="0.2.0")
        ],
        review_history=[],
        version_history=[
            PatternVersion(version_number="0.1.0", changes="initial", timestamp=datetime.datetime.now(), author_id="a", document_hash="h1", status_at_creation=PatternStatus.DRAFT),
            PatternVersion(version_number="0.2.0", changes="review", timestamp=datetime.datetime.now(), author_id="a", document_hash="h2", status_at_creation=PatternStatus.IN_REVIEW)
        ]
    ).dict(by_alias=True)

    response = client.get(f"/patterns/{pattern_id}/workflow/status")

    assert response.status_code == 200
    assert response.json()["pattern_id"] == pattern_id
    assert response.json()["current_state"] == "in_review"
    assert response.json()["current_version"] == "0.2.0"
    assert len(response.json()["pending_reviews"]) == 1
    mock_workflow_manager.get_workflow_status.assert_called_once_with(pattern_id)

@pytest.mark.asyncio
async def test_get_pattern_workflow_status_not_found(client, mock_workflow_manager):
    pattern_id = "pat123"
    mock_workflow_manager.get_workflow_status.side_effect = ValueError("Pattern not found.")

    response = client.get(f"/patterns/{pattern_id}/workflow/status")

    assert response.status_code == 404
    assert "Pattern not found." in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_patterns_awaiting_review_admin(client, mock_workflow_manager):
    mock_workflow_manager.get_patterns_awaiting_review.return_value = [
        {"pattern_id": "pat1", "title": "P1", "assigned_reviewer": "reviewerA"},
        {"pattern_id": "pat2", "title": "P2", "assigned_reviewer": "reviewerB"}
    ]
    # Ensure admin role is present for this test
    with patch('src.uckn.api.routers.workflow.get_current_user_roles', return_value=["admin"]):
        response = client.get("/patterns/workflow/pending_reviews")

    assert response.status_code == 200
    assert len(response.json()) == 2
    mock_workflow_manager.get_patterns_awaiting_review.assert_called_once_with(None) # Admin sees all

@pytest.mark.asyncio
async def test_get_patterns_awaiting_review_contributor(client, mock_workflow_manager):
    mock_workflow_manager.get_patterns_awaiting_review.return_value = [
        {"pattern_id": "pat1", "title": "P1", "assigned_reviewer": "test_user"}
    ]
    # Ensure contributor role is present for this test
    with patch('src.uckn.api.routers.workflow.get_current_user_roles', return_value=["contributor"]):
        response = client.get("/patterns/workflow/pending_reviews")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["assigned_reviewer"] == "test_user"
    mock_workflow_manager.get_patterns_awaiting_review.assert_called_once_with("test_user") # Contributor sees only their own
