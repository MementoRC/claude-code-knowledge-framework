from pathlib import Path
from unittest.mock import Mock

import pytest

from src.uckn.core.atoms.tech_stack_detector import TechStackDetector
from src.uckn.core.molecules.issue_detection_rules import IssueDetectionRules


@pytest.fixture
def mock_tech_stack_detector():
    mock = Mock(spec=TechStackDetector)
    # Default return value for analyze_project
    mock.analyze_project.return_value = {
        "languages": [],
        "package_managers": [],
        "frameworks": [],
        "testing": [],
        "ci_cd": [],
        "files": [],  # Added for potential file checks in rules
    }
    return mock


@pytest.fixture
def issue_detection_rules(mock_tech_stack_detector):
    return IssueDetectionRules(tech_stack_detector=mock_tech_stack_detector)


def test_analyze_project_for_rules_calls_tech_stack_detector(
    issue_detection_rules, mock_tech_stack_detector
):
    project_path = "/tmp/test_project"
    Path(project_path).mkdir(
        parents=True, exist_ok=True
    )  # Ensure path exists for TechStackDetector
    issue_detection_rules.analyze_project_for_rules(project_path)
    mock_tech_stack_detector.analyze_project.assert_called_once_with(project_path)


def test_detect_dependency_conflicts_python_no_lock_file(
    issue_detection_rules, mock_tech_stack_detector
):
    mock_tech_stack_detector.analyze_project.return_value = {
        "languages": ["Python"],
        "package_managers": ["pip"],
        "project_path": Path("/tmp/python_proj"),
    }
    Path("/tmp/python_proj").mkdir(parents=True, exist_ok=True)

    issues = issue_detection_rules.analyze_project_for_rules("/tmp/python_proj")
    assert any(
        issue["type"] == "dependency_conflict"
        and "lack of strict dependency locking" in issue["description"]
        for issue in issues
    )


def test_detect_dependency_conflicts_javascript_no_lock_file(
    issue_detection_rules, mock_tech_stack_detector
):
    mock_tech_stack_detector.analyze_project.return_value = {
        "languages": ["JavaScript"],
        "package_managers": ["npm"],
    }
    Path("/tmp/js_proj").mkdir(parents=True, exist_ok=True)
    # Remove package-lock.json if it exists to trigger the rule
    lock_file = Path("/tmp/js_proj") / "package-lock.json"
    if lock_file.exists():
        lock_file.unlink()

    issues = issue_detection_rules.analyze_project_for_rules("/tmp/js_proj")
    assert any(
        issue["type"] == "dependency_conflict"
        and "missing 'package-lock.json'" in issue["description"]
        for issue in issues
    )


def test_detect_build_failures_python_no_dockerfile(
    issue_detection_rules, mock_tech_stack_detector
):
    mock_tech_stack_detector.analyze_project.return_value = {
        "languages": ["Python"],
        "files": [],  # Simulate no Dockerfile
        "project_path": Path("/tmp/python_proj_no_docker"),
    }
    Path("/tmp/python_proj_no_docker").mkdir(parents=True, exist_ok=True)

    issues = issue_detection_rules.analyze_project_for_rules(
        "/tmp/python_proj_no_docker"
    )
    assert any(
        issue["type"] == "build_failure_risk"
        and "No Dockerfile detected" in issue["description"]
        for issue in issues
    )


def test_detect_test_flakiness_pytest_detected(
    issue_detection_rules, mock_tech_stack_detector
):
    mock_tech_stack_detector.analyze_project.return_value = {
        "testing": ["pytest"],
        "project_path": Path("/tmp/pytest_proj"),
    }
    Path("/tmp/pytest_proj").mkdir(parents=True, exist_ok=True)

    issues = issue_detection_rules.analyze_project_for_rules("/tmp/pytest_proj")
    assert any(
        issue["type"] == "test_flakiness_risk"
        and "Potential for test flakiness" in issue["description"]
        for issue in issues
    )


def test_detect_performance_bottlenecks_python(
    issue_detection_rules, mock_tech_stack_detector
):
    mock_tech_stack_detector.analyze_project.return_value = {
        "languages": ["Python"],
        "project_path": Path("/tmp/perf_python"),
    }
    Path("/tmp/perf_python").mkdir(parents=True, exist_ok=True)

    issues = issue_detection_rules.analyze_project_for_rules("/tmp/perf_python")
    assert any(
        issue["type"] == "performance_bottleneck_risk"
        and "asynchronous programming" in issue["description"]
        for issue in issues
    )


def test_detect_security_vulnerabilities_javascript(
    issue_detection_rules, mock_tech_stack_detector
):
    mock_tech_stack_detector.analyze_project.return_value = {
        "languages": ["JavaScript"],
        "project_path": Path("/tmp/sec_js"),
    }
    Path("/tmp/sec_js").mkdir(parents=True, exist_ok=True)

    issues = issue_detection_rules.analyze_project_for_rules("/tmp/sec_js")
    assert any(
        issue["type"] == "security_vulnerability_risk"
        and "XSS and CSRF" in issue["description"]
        for issue in issues
    )


def test_no_issues_detected_for_empty_stack(
    issue_detection_rules, mock_tech_stack_detector
):
    mock_tech_stack_detector.analyze_project.return_value = {
        "languages": [],
        "package_managers": [],
        "frameworks": [],
        "testing": [],
        "ci_cd": [],
        "files": [],
        "project_path": Path("/tmp/empty_proj"),
    }
    Path("/tmp/empty_proj").mkdir(parents=True, exist_ok=True)

    issues = issue_detection_rules.analyze_project_for_rules("/tmp/empty_proj")
    assert len(issues) == 0
