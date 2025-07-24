"""
Error simulation and error solution test fixtures for UCKN.

Provides:
- Error scenario samples
- Error solution samples
- Error scenario generator
"""

import pytest


@pytest.fixture
def sample_error_solutions():
    """
    Returns a list of sample error solutions for testing.
    """
    return [
        {
            "id": "error-solution-1",
            "error_category": "ImportError",
            "resolution_steps": "Check module path; reinstall package",
            "avg_resolution_time": 2.5,
            "document": "To fix ImportError, ensure the module is installed and the path is correct.",
            "metadata": {
                "solution_id": "error-solution-1",
                "error_category": "ImportError",
                "resolution_steps": "Check module path; reinstall package",
                "avg_resolution_time": 2.5,
                "created_at": "2024-06-28T12:00:00Z",
                "updated_at": "2024-06-28T12:00:00Z",
            },
        },
        {
            "id": "error-solution-2",
            "error_category": "TimeoutError",
            "resolution_steps": "Increase timeout; check network connectivity",
            "avg_resolution_time": 5.0,
            "document": "TimeoutError can be resolved by increasing the timeout or checking the network.",
            "metadata": {
                "solution_id": "error-solution-2",
                "error_category": "TimeoutError",
                "resolution_steps": "Increase timeout; check network connectivity",
                "avg_resolution_time": 5.0,
                "created_at": "2024-06-28T12:00:00Z",
                "updated_at": "2024-06-28T12:00:00Z",
            },
        },
    ]


@pytest.fixture
def error_scenario_samples():
    """
    Returns a list of error scenario samples for simulation.
    """
    return [
        {"type": "network", "message": "Simulated network failure"},
        {"type": "timeout", "message": "Simulated timeout"},
        {"type": "resource", "message": "Simulated resource exhaustion"},
        {"type": "generic", "message": "Simulated generic error"},
    ]
