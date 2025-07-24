from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

from src.uckn.core.atoms.tech_stack_detector import TechStackDetector
from src.uckn.core.molecules.error_solution_manager import ErrorSolutionManager
from src.uckn.core.molecules.issue_detection_rules import IssueDetectionRules
from src.uckn.core.molecules.issue_prediction_models import IssuePredictionModels
from src.uckn.core.molecules.pattern_analytics import PatternAnalytics
from src.uckn.core.organisms.predictive_issue_detector import PredictiveIssueDetector


@pytest.fixture
def mock_tech_stack_detector():
    mock = Mock(spec=TechStackDetector)
    mock.analyze_project.return_value = {
        "languages": ["Python"],
        "package_managers": ["pip"],
        "frameworks": [],
        "testing": ["pytest"],
        "ci_cd": ["GitHub Actions"],
    }
    return mock


@pytest.fixture
def mock_issue_detection_rules():
    mock = Mock(spec=IssueDetectionRules)
    mock.analyze_project_for_rules.return_value = [
        {
            "type": "dependency_conflict",
            "description": "Rule-based: Potential dependency conflicts.",
            "severity": "medium",
            "confidence": 0.7,
            "preventive_measure": "Use dependency locking.",
        }
    ]
    return mock


@pytest.fixture
def mock_issue_prediction_models():
    mock = Mock(spec=IssuePredictionModels)
    mock.is_available.return_value = True
    mock.predict.return_value = [
        {
            "type": "ml_performance_issue",
            "description": "ML-based: Predicted performance bottleneck.",
            "severity": "high",
            "confidence": 0.85,
            "preventive_measure": "Optimize database queries.",
        }
    ]
    mock.train_model.return_value = True
    mock.feature_extract.return_value = [0.1, 0.2, 0.3]  # Dummy features
    return mock


@pytest.fixture
def mock_error_solution_manager():
    mock = Mock(spec=ErrorSolutionManager)
    mock.add_error_solution.return_value = "new_solution_id"
    return mock


@pytest.fixture
def mock_pattern_analytics():
    mock = Mock(spec=PatternAnalytics)
    mock.record_outcome.return_value = True
    return mock


@pytest.fixture
def predictive_issue_detector(
    mock_tech_stack_detector,
    mock_issue_detection_rules,
    mock_issue_prediction_models,
    mock_error_solution_manager,
    mock_pattern_analytics,
):
    return PredictiveIssueDetector(
        tech_stack_detector=mock_tech_stack_detector,
        issue_detection_rules=mock_issue_detection_rules,
        issue_prediction_models=mock_issue_prediction_models,
        error_solution_manager=mock_error_solution_manager,
        pattern_analytics=mock_pattern_analytics,
    )


def test_detect_issues_combines_rule_and_ml_results(
    predictive_issue_detector,
    mock_tech_stack_detector,
    mock_issue_detection_rules,
    mock_issue_prediction_models,
):
    project_path = "/tmp/test_project"
    Path(project_path).mkdir(
        parents=True, exist_ok=True
    )  # Ensure path exists for TechStackDetector

    issues = predictive_issue_detector.detect_issues(project_path)

    mock_tech_stack_detector.analyze_project.assert_called_once_with(project_path)
    mock_issue_detection_rules.analyze_project_for_rules.assert_called_once_with(
        project_path
    )
    mock_issue_prediction_models.predict.assert_called_once()

    assert len(issues) == 2
    assert any(issue["type"] == "dependency_conflict" for issue in issues)
    assert any(issue["type"] == "ml_performance_issue" for issue in issues)


def test_detect_issues_handles_ml_model_unavailability(
    predictive_issue_detector, mock_issue_prediction_models
):
    mock_issue_prediction_models.is_available.return_value = False
    project_path = "/tmp/test_project_no_ml"
    Path(project_path).mkdir(parents=True, exist_ok=True)

    issues = predictive_issue_detector.detect_issues(project_path)

    mock_issue_prediction_models.predict.assert_not_called()
    assert len(issues) == 1  # Only rule-based issues should be present


def test_provide_feedback_records_data(
    predictive_issue_detector, mock_error_solution_manager, mock_pattern_analytics
):
    issue_id = "test_issue_123"
    project_id = "proj_abc"
    outcome = "resolved"
    resolution_details = "Updated dependency versions."
    time_to_resolve = 30.5

    success = predictive_issue_detector.provide_feedback(
        issue_id=issue_id,
        project_id=project_id,
        outcome=outcome,
        resolution_details=resolution_details,
        time_to_resolve_minutes=time_to_resolve,
        feedback_data={"source": "CI/CD"},
    )

    assert success
    # In a real scenario, you'd assert calls to error_solution_manager or pattern_analytics
    # For now, we just check the method returns True as per its current mock behavior.
    # The internal logging of feedback_record is not directly testable here without mocking logging.


def test_detect_issues_with_code_snippet_and_context(
    predictive_issue_detector, mock_issue_prediction_models
):
    project_path = "/tmp/test_project_snippet"
    Path(project_path).mkdir(parents=True, exist_ok=True)
    code_snippet = "def my_func(): pass"
    context_description = "New feature implementation"
    project_id = "proj_xyz"

    predictive_issue_detector.detect_issues(
        project_path=project_path,
        code_snippet=code_snippet,
        context_description=context_description,
        project_id=project_id,
    )

    # Verify that ML model's predict method received the additional context
    mock_issue_prediction_models.predict.assert_called_once()
    args, kwargs = mock_issue_prediction_models.predict.call_args
    ml_input_data = args[0]
    assert ml_input_data["code_snippet"] == code_snippet
    assert ml_input_data["context_description"] == context_description
    assert ml_input_data["project_id"] == project_id
