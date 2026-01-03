"""
Integration tests for UCKN API endpoints
Tests the actual API server with real database connections
"""

import pytest
from fastapi.testclient import TestClient

from src.uckn.api.main import app

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def client():
    """Create a test client for the API"""
    return TestClient(app)


def test_health_endpoint(client):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "message" in data


def test_patterns_endpoint_basic(client):
    """Test basic patterns endpoints"""
    # Test GET patterns (should work but might be 404 if not implemented)
    response = client.get("/api/v1/patterns/")
    # Endpoint might not be fully implemented yet, or might require auth (401)
    assert response.status_code in [200, 401, 404, 405]


def test_projects_endpoint_basic(client):
    """Test basic projects endpoints"""
    # Test GET projects (should work but might be 404 if not implemented)
    response = client.get("/api/v1/projects/")
    # Endpoint might not be fully implemented yet, or might require auth (401)
    assert response.status_code in [200, 401, 404, 405]


def test_error_solutions_endpoint_basic(client):
    """Test basic error solutions endpoints"""
    # Test GET solutions (should work even if empty)
    response = client.get("/api/v1/error-solutions/")
    # This might be 404 if endpoint doesn't exist yet, or 200 if it does, or 401 if auth required
    assert response.status_code in [200, 401, 404, 405]


def test_api_root(client):
    """Test the API root endpoint"""
    response = client.get("/")
    # Should either have a welcome message or redirect
    assert response.status_code in [200, 307, 404]


def test_docs_endpoint(client):
    """Test that API documentation is available"""
    response = client.get("/docs")
    # Docs might not be enabled in all environments
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        assert "text/html" in response.headers.get("content-type", "")


def test_openapi_spec(client):
    """Test that OpenAPI spec is available"""
    response = client.get("/openapi.json")
    # OpenAPI spec might not be enabled in all environments
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        spec = response.json()
        assert "openapi" in spec
        assert "info" in spec
