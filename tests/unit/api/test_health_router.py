"""
Tests for health monitoring API endpoints.
"""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src.uckn.api.dependencies import get_knowledge_manager

# Import the main FastAPI app and the dependency
from src.uckn.api.main import app
from src.uckn.core.organisms.knowledge_manager import KnowledgeManager


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_knowledge_manager():
    """Mock KnowledgeManager instance."""
    return Mock(spec=KnowledgeManager)


@pytest.fixture(autouse=True)
def override_knowledge_manager_dependency(mock_knowledge_manager):
    """
    Overrides the get_knowledge_manager dependency for testing.
    """
    app.dependency_overrides[get_knowledge_manager] = lambda: mock_knowledge_manager
    yield
    app.dependency_overrides = {}  # Clean up after test


@pytest.mark.unit
def test_health_check(client):
    """Test basic health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "message" in data


@pytest.mark.unit
def test_system_status_healthy(client, mock_knowledge_manager):
    """Test system status endpoint when healthy."""
    mock_knowledge_manager.get_health_status.return_value = {
        "unified_db_available": True,
        "components": {
            "pattern_manager": "healthy",
            "error_solution_manager": "healthy",
        },
    }

    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "components" in data
    assert data["version"] == "1.0.0"
    mock_knowledge_manager.get_health_status.assert_called_once()


@pytest.mark.unit
def test_system_status_degraded(client, mock_knowledge_manager):
    """Test system status endpoint when degraded."""
    mock_knowledge_manager.get_health_status.return_value = {
        "unified_db_available": False,
        "components": {
            "pattern_manager": "degraded",
            "error_solution_manager": "degraded",
        },
    }

    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert "components" in data
    mock_knowledge_manager.get_health_status.assert_called_once()


@pytest.mark.unit
def test_system_status_error(client, mock_knowledge_manager):
    """Test system status endpoint when an error occurs in the knowledge manager."""
    mock_knowledge_manager.get_health_status.side_effect = Exception(
        "Simulated KM error"
    )

    response = client.get("/api/v1/status")
    assert (
        response.status_code == 200
    )  # The endpoint itself handles the exception and returns a status
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["components"] == {}
    mock_knowledge_manager.get_health_status.assert_called_once()
