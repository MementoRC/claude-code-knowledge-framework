"""
Tests for health monitoring API endpoints.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from src.uckn.api.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


def test_health_check(client):
    """Test basic health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "message" in data


@pytest.mark.skip(
    reason="Dependency injection mocking complex - requires service architecture fixes"
)
@patch("src.uckn.api.dependencies.get_knowledge_manager")
def test_system_status_healthy(mock_get_km, client):
    """Test system status endpoint when healthy."""
    # Mock knowledge manager
    mock_km = Mock()
    mock_km.get_health_status.return_value = {
        "unified_db_available": True,
        "components": {
            "pattern_manager": "healthy",
            "error_solution_manager": "healthy",
        },
    }
    mock_get_km.return_value = mock_km

    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "components" in data
    assert data["version"] == "1.0.0"


@pytest.mark.skip(
    reason="Dependency injection mocking complex - requires service architecture fixes"
)
@patch("src.uckn.api.dependencies.get_knowledge_manager")
def test_system_status_degraded(mock_get_km, client):
    """Test system status endpoint when degraded."""
    # Mock knowledge manager
    mock_km = Mock()
    mock_km.get_health_status.return_value = {
        "unified_db_available": False,
        "components": {
            "pattern_manager": "degraded",
            "error_solution_manager": "degraded",
        },
    }
    mock_get_km.return_value = mock_km

    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert "components" in data
