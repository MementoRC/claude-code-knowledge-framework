import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime

from src.uckn.api.routers.predictions import router
from src.uckn.core.organisms.predictive_issue_detector import PredictiveIssueDetector
from src.uckn.api.dependencies import get_predictive_issue_detector

# Create a TestClient for the router
client = TestClient(router)

@pytest.fixture
def mock_predictive_issue_detector():
    mock = Mock(spec=PredictiveIssueDetector)
    mock.detect_issues.return_value = [
        {
            "type": "mock_issue_type",
            "description": "This is a mock detected issue.",
            "severity": "medium",
            "confidence": 0.75,
            "preventive_measure": "Take mock action."
        }
    ]
    mock.provide_feedback.return_value = True
    return mock

@pytest.fixture(autouse=True)
def override_dependency(mock_predictive_issue_detector):
    """
    Overrides the get_predictive_issue_detector dependency for testing.
    """
    router.dependency_overrides[get_predictive_issue_detector] = lambda: mock_predictive_issue_detector
    yield
    router.dependency_overrides = {} # Clean up after test

def test_detect_issues_endpoint_success(mock_predictive_issue_detector):
    request_payload = {
        "project_path": "/app/test_project",
        "code_snippet": "print('hello')",
        "context_description": "Testing a new feature",
        "project_id": "proj123"
    }
    response = client.post("/predictions/detect", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()
    assert "timestamp" in response_data
    assert response_data["message"] == "Prediction completed successfully."
    assert len(response_data["issues"]) == 1
    assert response_data["issues"][0]["type"] == "mock_issue_type"
    assert response_data["issues"][0]["confidence"] == 0.75

    mock_predictive_issue_detector.detect_issues.assert_called_once_with(
        project_path="/app/test_project",
        code_snippet="print('hello')",
        context_description="Testing a new feature",
        project_id="proj123"
    )

def test_detect_issues_endpoint_minimal_payload(mock_predictive_issue_detector):
    request_payload = {
        "project_path": "/app/minimal_project"
    }
    response = client.post("/predictions/detect", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data["issues"]) == 1
    mock_predictive_issue_detector.detect_issues.assert_called_once_with(
        project_path="/app/minimal_project",
        code_snippet=None,
        context_description=None,
        project_id=None
    )

def test_detect_issues_endpoint_internal_error(mock_predictive_issue_detector):
    mock_predictive_issue_detector.detect_issues.side_effect = Exception("Simulated internal error")
    request_payload = {
        "project_path": "/app/error_project"
    }
    response = client.post("/predictions/detect", json=request_payload)

    assert response.status_code == 500
    assert "detail" in response.json()
    assert "Failed to detect issues" in response.json()["detail"]

def test_submit_feedback_endpoint_success(mock_predictive_issue_detector):
    request_payload = {
        "issue_id": "issue_abc_123",
        "project_id": "proj123",
        "outcome": "resolved",
        "resolution_details": "Fixed a bug",
        "time_to_resolve_minutes": 60.5,
        "feedback_data": {"user": "test_user"}
    }
    response = client.post("/predictions/feedback", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["message"] == "Feedback recorded successfully."

    mock_predictive_issue_detector.provide_feedback.assert_called_once_with(
        issue_id="issue_abc_123",
        project_id="proj123",
        outcome="resolved",
        resolution_details="Fixed a bug",
        time_to_resolve_minutes=60.5,
        feedback_data={"user": "test_user"}
    )

def test_submit_feedback_endpoint_minimal_payload(mock_predictive_issue_detector):
    request_payload = {
        "issue_id": "issue_minimal",
        "outcome": "false_positive"
    }
    response = client.post("/predictions/feedback", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    mock_predictive_issue_detector.provide_feedback.assert_called_once_with(
        issue_id="issue_minimal",
        project_id=None,
        outcome="false_positive",
        resolution_details=None,
        time_to_resolve_minutes=None,
        feedback_data=None
    )

def test_submit_feedback_endpoint_internal_error(mock_predictive_issue_detector):
    mock_predictive_issue_detector.provide_feedback.side_effect = Exception("Simulated feedback error")
    request_payload = {
        "issue_id": "issue_error",
        "outcome": "resolved"
    }
    response = client.post("/predictions/feedback", json=request_payload)

    assert response.status_code == 500
    assert "detail" in response.json()
    assert "Failed to submit feedback" in response.json()["detail"]

